import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import Layout from '../components/Layout';
import { api } from '../api';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, hourlyData] = await Promise.all([
        api.stats.get(),
        api.stats.hourly(),
      ]);
      setStats(statsData);
      setChartData({
        labels: hourlyData.map(d => new Date(d.hour).getHours() + ':00'),
        datasets: [{
          label: 'Videos',
          data: hourlyData.map(d => d.count),
          backgroundColor: '#3b82f6',
        }],
      });
    } catch (err) {
      console.error('Failed to load stats:', err);
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
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Videos processed</div>
          <div className="text-3xl font-bold">{stats?.total_videos ?? '-'}</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Total users</div>
          <div className="text-3xl font-bold">{stats?.total_users ?? '-'}</div>
        </div>
        <div className="bg-green-800 rounded-lg p-6">
          <div className="text-green-300 text-sm">Active users</div>
          <div className="text-3xl font-bold">{stats?.active_users ?? '-'}</div>
        </div>
        <div className="bg-red-900 rounded-lg p-6">
          <div className="text-red-300 text-sm">Blocked users</div>
          <div className="text-3xl font-bold">{stats?.blocked_users ?? '-'}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Avg processing</div>
          <div className="text-3xl font-bold">
            {stats ? (stats.avg_time_ms / 1000).toFixed(1) + 's' : '-'}
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-gray-400 text-sm">Errors</div>
          <div className="text-3xl font-bold">{stats?.errors ?? '-'}</div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Activity (24h)</h2>
        {chartData && (
          <Bar
            data={chartData}
            options={{
              responsive: true,
              plugins: { legend: { display: false } },
              scales: {
                x: { grid: { color: '#374151' } },
                y: { grid: { color: '#374151' } },
              },
            }}
          />
        )}
      </div>
    </Layout>
  );
}
