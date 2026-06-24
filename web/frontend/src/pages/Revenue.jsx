import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import Layout from '../components/Layout';
import { api } from '../api';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function Revenue() {
  const [revenue, setRevenue] = useState(null);
  const [monthly, setMonthly] = useState([]);
  const [packages, setPackages] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [revData, monthlyData, pkgData, recentData] = await Promise.all([
        api.revenue.get(),
        api.revenue.monthly(),
        api.revenue.packages(),
        api.revenue.recent(),
      ]);
      setRevenue(revData);
      setMonthly(monthlyData);
      setPackages(pkgData);
      setRecent(recentData);
    } catch (err) {
      console.error('Failed to load revenue:', err);
    } finally {
      setLoading(false);
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
      <h1 className="text-3xl font-bold mb-8">Revenue</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Total Revenue</div>
          <div className="text-3xl font-bold">
            ⭐{revenue?.total_stars ?? 0} / ₽{revenue?.total_rub ?? 0}
          </div>
        </div>
        <div className="bg-yellow-900 rounded-lg p-6">
          <div className="text-yellow-300 text-sm">⭐ Telegram Stars</div>
          <div className="text-3xl font-bold">{revenue?.total_stars ?? 0}</div>
        </div>
        <div className="bg-green-800 rounded-lg p-6">
          <div className="text-green-300 text-sm">💳 Rubles</div>
          <div className="text-3xl font-bold">₽{revenue?.total_rub ?? 0}</div>
        </div>
        <div className="bg-blue-800 rounded-lg p-6">
          <div className="text-blue-300 text-sm">Conversion</div>
          <div className="text-3xl font-bold">
            {revenue?.conversion ?? 0}% ({revenue?.premium_users ?? 0}/{revenue?.total_users ?? 0})
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Revenue by Month</h2>
          {monthly.length > 0 && (
            <Bar
              data={{
                labels: monthly.map(d => d.month),
                datasets: [
                  { label: '⭐ Stars', data: monthly.map(d => d.stars), backgroundColor: '#eab308' },
                  { label: '₽ Rubles', data: monthly.map(d => d.rub), backgroundColor: '#22c55e' },
                ],
              }}
              options={{
                responsive: true,
                plugins: { legend: { labels: { color: '#fff' } } },
                scales: {
                  x: { grid: { color: '#374151' } },
                  y: { grid: { color: '#374151' } },
                },
              }}
            />
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Revenue by Package</h2>
          <div className="space-y-3">
            {packages.map((p, i) => (
              <div key={i} className="flex justify-between items-center bg-gray-700 rounded p-3">
                <div>
                  <div className="font-bold">{p.name}</div>
                  <div className="text-sm text-gray-400">{p.count} sales</div>
                </div>
                <div className="text-right">
                  <div className="font-bold">{p.percentage}%</div>
                  <div className="text-sm text-gray-400">⭐{p.total}</div>
                </div>
              </div>
            ))}
            {packages.length === 0 && (
              <div className="text-gray-500 text-center py-4">No data</div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Recent Payments</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="py-2">User</th>
                <th className="py-2">Package</th>
                <th className="py-2">Amount</th>
                <th className="py-2">Status</th>
                <th className="py-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((p) => (
                <tr key={p.id} className="border-b border-gray-700">
                  <td className="py-2">{p.user}</td>
                  <td className="py-2">{p.package}</td>
                  <td className="py-2">
                    {p.currency === 'stars' ? '⭐' : '₽'}{p.amount}
                  </td>
                  <td className="py-2">
                    <span className={`px-2 py-1 rounded text-xs ${p.status === 'completed' ? 'bg-green-800' : 'bg-yellow-800'}`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="py-2">{new Date(p.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr>
                  <td colSpan="5" className="py-4 text-center text-gray-500">No payments</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
