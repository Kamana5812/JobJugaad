import { useEffect, useState } from 'react';
import axios from '../api';
import { useParams } from 'react-router-dom';

function DriveMatches() {
  const { id } = useParams(); // job id
  const token = localStorage.getItem('access_token');
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadMatches = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`/recruiter/jobs/${id}/matches`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMatches(res.data);
    } catch (err) {
      console.error(err);
      alert('Failed to fetch matches');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadMatches();
  }, [id]);

  const handleOverride = async (matchId, status) => {
    try {
      await axios.post(`/recruiter/matches/${matchId}/override`, { status }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert(`Candidate ${status}`);
      loadMatches(); // Refresh to see updated override_status
    } catch (err) {
      console.error(err);
      alert('Failed to override');
    }
  };

  if (loading) return <p>Loading matches…</p>;

  return (
    <div className="max-w-3xl mx-auto mt-8 p-4 border rounded">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl">Candidate Matches</h2>
        <button onClick={loadMatches} className="bg-indigo-600 text-white px-4 py-2 rounded">
          Run AI Matching
        </button>
      </div>
      {matches.length === 0 && <p>No candidates found.</p>}
      {matches.map((m) => (
        <div key={m.id} className="mb-4 p-2 border">
          <p><strong>Student ID:</strong> {m.student_id}</p>
          <p><strong>Score:</strong> {m.match_score}</p>
          {m.explanation && <p><strong>Explanation:</strong> {m.explanation}</p>}
          {m.factor_breakdown && (
            <div>
              <p><strong>Breakdown:</strong></p>
              <ul className="list-disc ml-5">
                {Object.entries(m.factor_breakdown).map(([k, v]) => (
                  <li key={k}>{k}: {v}</li>
                ))}
              </ul>
            </div>
          )}
          {m.override_status && (
            <p className="mt-2 text-indigo-600 font-bold uppercase">
              Manual Override: {m.override_status}
            </p>
          )}
          <div className="mt-4 flex space-x-2">
            <button onClick={() => handleOverride(m.id, 'promoted')} className="bg-green-500 text-white px-3 py-1 rounded text-sm">
              Promote
            </button>
            <button onClick={() => handleOverride(m.id, 'rejected')} className="bg-red-500 text-white px-3 py-1 rounded text-sm">
              Reject
            </button>
            {m.override_status && (
              <button onClick={() => handleOverride(m.id, 'none')} className="bg-gray-400 text-white px-3 py-1 rounded text-sm">
                Clear Override
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default DriveMatches;
