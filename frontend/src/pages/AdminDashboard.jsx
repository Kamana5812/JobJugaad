import { useEffect, useState } from 'react';
import axios from '../api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

function AdminDashboard() {
  const token = localStorage.getItem('access_token');
  const [analytics, setAnalytics] = useState(null);
  const [atRisk, setAtRisk] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const [resAnalytics, resAtRisk] = await Promise.all([
          axios.get('/admin/analytics', { headers }),
          axios.get('/admin/at-risk', { headers })
        ]);
        setAnalytics(resAnalytics.data);
        setAtRisk(resAtRisk.data);
      } catch (err) {
        console.error(err);
        alert('Failed to fetch admin data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [token]);

  if (loading) return <p className="p-8 text-center text-gray-500">Loading Dashboard...</p>;

  return (
    <div className="max-w-6xl mx-auto mt-8 p-4">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">Admin Analytics Dashboard</h1>

      {/* KPI Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="p-6 bg-white rounded-lg shadow border border-gray-200">
          <h3 className="text-sm text-gray-500 uppercase tracking-wider">Total Students</h3>
          <p className="text-3xl font-bold text-indigo-600 mt-2">{analytics?.total_students || 0}</p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow border border-gray-200">
          <h3 className="text-sm text-gray-500 uppercase tracking-wider">Active Drives</h3>
          <p className="text-3xl font-bold text-indigo-600 mt-2">{analytics?.total_drives || 0}</p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow border border-gray-200">
          <h3 className="text-sm text-gray-500 uppercase tracking-wider">Total Matches</h3>
          <p className="text-3xl font-bold text-indigo-600 mt-2">{analytics?.total_matches || 0}</p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow border border-gray-200">
          <h3 className="text-sm text-gray-500 uppercase tracking-wider">Scheduled Interviews</h3>
          <p className="text-3xl font-bold text-indigo-600 mt-2">{analytics?.total_interviews || 0}</p>
        </div>
      </div>

      {/* Recharts: Matches by Branch */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-8">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Matches by Branch</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analytics?.matches_by_branch || []} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#4f46e5" name="Matches" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* At-Risk Students Table */}
      <div className="bg-white p-6 rounded-lg shadow border border-gray-200">
        <h2 className="text-xl font-bold mb-4 text-red-600">At-Risk Students Action Center</h2>
        {atRisk.length === 0 ? (
          <p className="text-gray-500">No students are currently flagged as at risk.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contributing Factors</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recommended Intervention</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {atRisk.map((student) => (
                  <tr key={student.student_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {student.student_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      <ul className="list-disc pl-5">
                        {student.factors.map((f, i) => <li key={i}>{f}</li>)}
                      </ul>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <span className="px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                        {student.recommendation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
