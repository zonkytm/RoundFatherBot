import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { api } from '../api';

const statusColors = {
  pending: 'bg-yellow-600',
  sending: 'bg-blue-600',
  done: 'bg-green-600',
  failed: 'bg-red-600',
};

export default function Mailings() {
  const [mailings, setMailings] = useState([]);
  const [presets, setPresets] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showLogs, setShowLogs] = useState(null);
  const [logs, setLogs] = useState([]);
  const [form, setForm] = useState({
    name: '',
    text: '',
    target: 'all',
    type: 'once',
    scheduled_at: '',
    cron_expression: '',
    schedule_mode: 'cron',
  });

  useEffect(() => {
    loadMailings();
    const interval = setInterval(loadMailings, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadMailings = async () => {
    try {
      const data = await api.mailings.list();
      setMailings(data);
    } catch (err) {
      console.error('Failed to load mailings:', err);
    }
  };

  const loadPresets = async () => {
    try {
      const data = await api.presets.list();
      setPresets(data);
    } catch (err) {
      console.error('Failed to load presets:', err);
    }
  };

  const handleCreate = async () => {
    const body = {
      name: form.name,
      text: form.text,
      target: form.target,
    };

    if (form.type === 'delayed') {
      body.scheduled_at = form.scheduled_at;
    } else if (form.type === 'recurring') {
      body.cron_expression = form.schedule_mode === 'cron'
        ? form.cron_expression
        : form.cron_expression;
    }

    try {
      await api.mailings.create(body);
      setShowCreate(false);
      setForm({ name: '', text: '', target: 'all', type: 'once', scheduled_at: '', cron_expression: '', schedule_mode: 'cron' });
      loadMailings();
    } catch (err) {
      alert('Failed to create mailing: ' + err.message);
    }
  };

  const handleToggleActive = async (id, active) => {
    try {
      await api.mailings.update(id, { is_active: active });
      loadMailings();
    } catch (err) {
      alert('Failed to update: ' + err.message);
    }
  };

  const handleResend = async (id) => {
    try {
      await api.mailings.send(id);
      loadMailings();
    } catch (err) {
      alert('Failed to resend: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this mailing?')) return;
    try {
      await api.mailings.delete(id);
      loadMailings();
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    }
  };

  const handleShowLogs = async (id) => {
    try {
      const data = await api.mailings.logs(id);
      setLogs(data);
      setShowLogs(id);
    } catch (err) {
      alert('Failed to load logs: ' + err.message);
    }
  };

  const openCreate = () => {
    loadPresets();
    setShowCreate(true);
  };

  return (
    <Layout>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Mailings</h1>
        <button
          onClick={openCreate}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
        >
          + Create
        </button>
      </div>

      <div className="space-y-3">
        {mailings.length === 0 ? (
          <div className="text-gray-500 text-center py-8">No mailings yet</div>
        ) : (
          mailings.map((m) => (
            <div key={m.id} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold">{m.name}</span>
                    <span className={`${statusColors[m.status] || 'bg-gray-600'} px-2 py-0.5 rounded text-xs`}>
                      {m.status}
                    </span>
                    {m.cron_expression && (
                      <span className="bg-purple-600 px-2 py-0.5 rounded text-xs">recurring</span>
                    )}
                    {m.scheduled_at && m.status === 'pending' && (
                      <span className="bg-indigo-600 px-2 py-0.5 rounded text-xs">
                        scheduled: {new Date(m.scheduled_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-400 truncate max-w-xl">{m.text}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Target: {m.target}
                    {(m.sent_count > 0 || m.failed_count > 0) && (
                      <> | Received: {m.sent_count} | Blocked: {m.failed_count}</>
                    )}
                    {m.cron_expression && <> | Cron: {m.cron_expression}</>}
                    {m.sent_at && <> | Last: {new Date(m.sent_at).toLocaleString()}</>}
                  </div>
                </div>
                <div className="flex gap-2 ml-4 flex-shrink-0">
                  <button
                    onClick={() => handleShowLogs(m.id)}
                    className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm"
                  >
                    History
                  </button>
                  {m.cron_expression && (
                    <button
                      onClick={() => handleToggleActive(m.id, !m.is_active)}
                      className={`px-3 py-1 rounded text-sm ${m.is_active ? 'bg-green-600' : 'bg-gray-600'}`}
                    >
                      {m.is_active ? 'On' : 'Off'}
                    </button>
                  )}
                  {m.status !== 'sending' && (
                    <>
                      <button
                        onClick={() => handleResend(m.id)}
                        className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                      >
                        Resend
                      </button>
                      <button
                        onClick={() => handleDelete(m.id)}
                        className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                      >
                        Delete
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-xl font-bold mb-4">New Mailing</h3>

            <input
              placeholder="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-gray-700 rounded px-3 py-2 mb-3"
            />
            <textarea
              placeholder="Message (HTML supported)"
              value={form.text}
              onChange={(e) => setForm({ ...form, text: e.target.value })}
              className="w-full bg-gray-700 rounded px-3 py-2 mb-3 h-24"
            />

            <select
              value={form.target}
              onChange={(e) => setForm({ ...form, target: e.target.value })}
              className="w-full bg-gray-700 rounded px-3 py-2 mb-4"
            >
              <option value="all">All users</option>
              <option value="admins">Admins only</option>
            </select>

            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">Type</label>
              <div className="flex gap-4">
                {['once', 'delayed', 'recurring'].map((type) => (
                  <label key={type} className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="m-type"
                      value={type}
                      checked={form.type === type}
                      onChange={(e) => setForm({ ...form, type: e.target.value })}
                    />
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </label>
                ))}
              </div>
            </div>

            {form.type === 'delayed' && (
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2">Send at</label>
                <input
                  type="datetime-local"
                  value={form.scheduled_at}
                  onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                  className="w-full bg-gray-700 rounded px-3 py-2"
                />
              </div>
            )}

            {form.type === 'recurring' && (
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-2">Cron expression</label>
                <input
                  placeholder="0 10 * * *"
                  value={form.cron_expression}
                  onChange={(e) => setForm({ ...form, cron_expression: e.target.value })}
                  className="w-full bg-gray-700 rounded px-3 py-2"
                />
                {presets.length > 0 && (
                  <div className="mt-2">
                    <label className="block text-sm text-gray-400 mb-1">Or select preset:</label>
                    <select
                      onChange={(e) => setForm({ ...form, cron_expression: e.target.value })}
                      className="w-full bg-gray-700 rounded px-3 py-2"
                    >
                      <option value="">-- Select preset --</option>
                      {presets.map((p) => (
                        <option key={p.id} value={p.cron_expr}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded flex-1"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Logs Modal */}
      {showLogs && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-xl font-bold mb-4">Send History</h3>
            <div className="space-y-2 mb-4">
              {logs.length === 0 ? (
                <div className="text-gray-500 text-center py-4">No history</div>
              ) : (
                logs.map((l) => (
                  <div key={l.id} className="bg-gray-700 rounded p-3">
                    <div className="text-sm">{new Date(l.sent_at).toLocaleString()}</div>
                    <div className="text-xs text-gray-400">
                      Sent: {l.sent_count} | Failed: {l.failed_count}
                    </div>
                  </div>
                ))
              )}
            </div>
            <button
              onClick={() => setShowLogs(null)}
              className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded w-full"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </Layout>
  );
}
