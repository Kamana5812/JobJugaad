import { useEffect, useState } from 'react';
import axios from '../api';

function Profile() {
  const token = localStorage.getItem('access_token');
  const [student, setStudent] = useState(null);
  const [ready, setReady] = useState(null);
  const [file, setFile] = useState(null);

  // Decode JWT on client‑side (no verification) to get user_id
  const payload = token ? JSON.parse(atob(token.split('.')[1])) : {};
  const userId = payload.user_id;

  useEffect(() => {
    if (!userId) return;
    const fetchProfile = async () => {
      try {
        const res = await axios.get('/students/me', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setStudent(res.data);
      } catch (err) {
        console.error('profile fetch error', err);
        alert('Failed to load profile');
      }
    };
    fetchProfile();
  }, [userId, token]);

  const uploadResume = async (e) => {
    e.preventDefault();
    if (!file) return alert('Select a PDF file first');
    const form = new FormData();
    form.append('file', file);
    try {
      await axios.post(`/students/${student.id}/resume`, form, {
        headers: { Authorization: `Bearer ${token}` },
      });
      alert('Resume uploaded and parsed');
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    }
  };

  const fetchReadiness = async () => {
    try {
      const res = await axios.get(`/students/${student.id}/readiness`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setReady(res.data);
    } catch (err) {
      console.error(err);
      alert('Readiness fetch failed');
    }
  };

  if (!student) return <p>Loading profile…</p>;

  return (
    <div className="max-w-2xl mx-auto mt-8 p-4 border rounded">
      <h2 className="text-2xl mb-4">Student Profile</h2>
      <p>Name: {student.name}</p>
      {/* Add more fields here as needed */}
      <form onSubmit={uploadResume} className="flex flex-col space-y-2 mt-4">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="p-2 border"
        />
        <button type="submit" className="bg-indigo-500 text-white p-2 rounded">
          Upload Resume
        </button>
      </form>
      <button
        onClick={fetchReadiness}
        className="mt-4 bg-green-600 text-white p-2 rounded"
      >
        Calculate Readiness
      </button>
      {ready && (
        <div className="mt-4 p-4 border bg-gray-50">
          <h3 className="text-lg">Readiness Score: {ready.score} ({ready.band})</h3>
          <p>Explanation: {ready.explanation}</p>
          <h4 className="mt-2">Breakdown</h4>
          <ul className="list-disc ml-5">
            {Object.entries(ready.breakdown).map(([k, v]) => (
              <li key={k}>{k.replace('_', ' ')}: {v}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default Profile;
