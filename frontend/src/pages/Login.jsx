import { useState } from 'react';
import axios from '../api';
import { useNavigate } from 'react-router-dom';

function Login({ setToken }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      const res = await axios.post('/auth/login', params);
      const token = res.data.access_token;
      setToken(token);
      localStorage.setItem('access_token', token);
      navigate('/profile');
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-4 border rounded">
      <h2 className="text-xl mb-4">Log In</h2>
      <form onSubmit={handleSubmit} className="flex flex-col space-y-3">
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required className="p-2 border" />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required className="p-2 border" />
        <button type="submit" className="bg-green-500 text-white p-2 rounded">Log In</button>
      </form>
    </div>
  );
}

export default Login;
