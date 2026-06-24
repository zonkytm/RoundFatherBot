import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { api } from '../api';

const LIMIT_KEYS = ['daily_limit', 'rate_limit_per_minute'];
const LIMIT_LABELS = {
  daily_limit: 'Daily Video Limit (free users)',
  rate_limit_per_minute: 'Rate Limit (per minute)',
};

export default function Settings() {
  const [settings, setSettings] = useState([]);
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.settings.get();
      setSettings(data.settings || []);
      setPackages(data.packages || []);
    } catch (err) {
      setError('Failed to load: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (msg) => {
    setToast(msg || 'Saved!');
    setTimeout(() => setToast(''), 2000);
  };

  const handleSaveLimit = async (key, value) => {
    if (!value || !/^\d+$/.test(value)) {
      alert('Must be a number');
      return;
    }
    try {
      const res = await api.settings.update(key, value);
      showToast(`${key} = ${value}`);
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  const handleSavePackage = async (pkg) => {
    const starsInput = document.querySelector(`[data-pkg="${pkg.id}"][data-field="price_stars"]`);
    const rubInput = document.querySelector(`[data-pkg="${pkg.id}"][data-field="price_rub"]`);
    const price_stars = parseInt(starsInput.value);
    const price_rub = parseInt(rubInput.value);

    if (isNaN(price_stars) || isNaN(price_rub) || price_stars < 0 || price_rub < 0) {
      alert('Prices must be positive numbers');
      return;
    }
    try {
      await api.settings.updatePackage(pkg.id, { price_stars, price_rub });
      showToast('Package updated');
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-8 text-gray-400">Loading...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <h1 className="text-3xl font-bold mb-8">Bot Settings</h1>

      {error && (
        <div className="bg-red-900 text-red-200 rounded p-4 mb-6">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-gray-800 rounded-lg p-6 min-w-0">
          <h2 className="text-xl font-bold mb-4 text-blue-400">Limits</h2>
          <div className="space-y-4">
            {LIMIT_KEYS.map((key) => {
              const s = settings.find(x => x.key === key);
              if (!s) return null;
              return (
                <LimitRow
                  key={key}
                  label={LIMIT_LABELS[key]}
                  value={s.value}
                  onSave={(val) => handleSaveLimit(key, val)}
                />
              );
            })}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 min-w-0">
          <h2 className="text-xl font-bold mb-4 text-yellow-400">Premium Packages</h2>
          <div className="space-y-4">
            {packages.map((pkg) => (
              <PackageRow key={pkg.id} pkg={pkg} onSave={() => handleSavePackage(pkg)} />
            ))}
          </div>
        </div>
      </div>

      {toast && (
        <div className="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg">
          {toast}
        </div>
      )}
    </Layout>
  );
}

function LimitRow({ label, value, onSave }) {
  const [inputValue, setInputValue] = useState(value);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave(inputValue);
    setSaving(false);
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
      <label className="text-sm text-gray-300 sm:w-48 shrink-0">{label}</label>
      <input
        type="number"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        min="0"
        className="min-w-0 flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
      />
      <button
        onClick={handleSave}
        disabled={saving}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm shrink-0 disabled:opacity-50"
      >
        {saving ? '...' : 'Save'}
      </button>
    </div>
  );
}

function PackageRow({ pkg, onSave }) {
  const [stars, setStars] = useState(pkg.price_stars);
  const [rub, setRub] = useState(pkg.price_rub);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave();
    setSaving(false);
  };

  return (
    <div className="bg-gray-700 rounded p-4 space-y-3">
      <div className="font-bold text-white">{pkg.name}</div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Stars</label>
          <input
            type="number"
            value={stars}
            onChange={(e) => setStars(e.target.value)}
            min="0"
            data-pkg={pkg.id}
            data-field="price_stars"
            className="w-full min-w-0 bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm focus:border-yellow-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">RUB</label>
          <input
            type="number"
            value={rub}
            onChange={(e) => setRub(e.target.value)}
            min="0"
            data-pkg={pkg.id}
            data-field="price_rub"
            className="w-full min-w-0 bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm focus:border-yellow-500 focus:outline-none"
          />
        </div>
      </div>
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
        >
          {saving ? '...' : 'Save'}
        </button>
      </div>
    </div>
  );
}
