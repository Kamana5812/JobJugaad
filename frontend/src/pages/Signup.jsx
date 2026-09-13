import { useState } from 'react';
import axios from '../api';
import { useNavigate } from 'react-router-dom';

function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('student');
  const [collegeId, setCollegeId] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('/auth/signup', {
        email,
        password,
        role,
        college_id: collegeId,
      });
      alert('Signup successful – you can now log in');
      navigate('/login');
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Signup failed');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-4 border rounded">
      <h2 className="text-xl mb-4">Sign Up</h2>
      <form onSubmit={handleSubmit} className="flex flex-col space-y-3">
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="p-2 border" />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required className="p-2 border" />
        <select value={role} onChange={e => setRole(e.target.value)} className="p-2 border">
          <option value="student">Student</option>
          <option value="recruiter">Recruiter</option>
          <option value="admin">Admin</option>
        </select>
        <input type="text" placeholder="College ID (UUID)" value={collegeId} onChange={e => setCollegeId(e.target.value)} required className="p-2 border" />
        <button type="submit" className="bg-blue-500 text-white p-2 rounded">Sign Up</button>
      </form>
    </div>
  );
}

export default Signup;
