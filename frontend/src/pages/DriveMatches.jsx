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
      const res = await axios.get(`/jobs/${id}/matches`, {
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

  if (loading) return <p>Loading matches…</p>;

  return (
    <div className="max-w-3xl mx-auto mt-8 p-4 border rounded">
      <h2 className="text-xl mb-4">Candidate Matches</h2>
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
        </div>
      ))}
    </div>
  );
}

export default DriveMatches;
