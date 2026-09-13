import { useState } from 'react';
import axios from '../api';
import { useNavigate } from 'react-router-dom';

function DriveCreate() {
  const token = localStorage.getItem('access_token');
  const [title, setTitle] = useState('');
  const [ctc, setCtc] = useState('');
  const [minCgpa, setMinCgpa] = useState('');
  const [branches, setBranches] = useState(''); // comma‑separated
  const [skills, setSkills] = useState(''); // e.g. Python:80,Java:70
  const navigate = useNavigate();

  const parseArray = (str) => str.split(',').map(s => s.trim()).filter(Boolean);
  const parseSkills = (str) => {
    const obj = {};
    str.split(',').forEach(pair => {
      const [skill, val] = pair.split(':').map(s => s.trim());
      if (skill && val) obj[skill] = Number(val);
    });
    return obj;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        title,
        ctc: ctc ? Number(ctc) : undefined,
        min_cgpa: minCgpa ? Number(minCgpa) : undefined,
        eligible_branches: parseArray(branches),
        required_skills: parseSkills(skills),
      };
      const res = await axios.post('/recruiter/jobs', payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
      alert('Drive created');
      // Navigate to matches page for this drive
      navigate(`/drives/${res.data.id}`);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Drive creation failed');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-4 border rounded">
      <h2 className="text-xl mb-4">Create Drive / Job</h2>
      <form onSubmit={handleSubmit} className="flex flex-col space-y-3">
        <input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} required className="p-2 border" />
        <input placeholder="CTC (optional)" value={ctc} onChange={e => setCtc(e.target.value)} className="p-2 border" />
        <input placeholder="Min CGPA (optional)" value={minCgpa} onChange={e => setMinCgpa(e.target.value)} className="p-2 border" />
        <input placeholder="Eligible branches (comma separated)" value={branches} onChange={e => setBranches(e.target.value)} className="p-2 border" />
        <input placeholder="Required skills (e.g. Python:80,Java:70)" value={skills} onChange={e => setSkills(e.target.value)} className="p-2 border" />
        <button type="submit" className="bg-indigo-500 text-white p-2 rounded">Create Drive</button>
      </form>
    </div>
  );
}

export default DriveCreate;
