import { useState, useContext } from 'react';
import { AuthContext } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function Signup() {
  const { signup } = useContext(AuthContext);
  const [formData, setFormData] = useState({ email: '', password: '', name: '', branch: '', cgpa: '' });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await signup({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        branch: formData.branch,
        cgpa: parseFloat(formData.cgpa)
      });
      navigate('/student/dashboard');
    } catch (err) {
      setError('Signup failed.');
    }
  };

  return (
    <div className="min-h-screen bg-navy flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-white">Create your Profile</h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && <div className="text-red-500 text-sm">{error}</div>}
            
            <div>
              <label className="block text-sm font-medium text-ink">Name</label>
              <input type="text" name="name" required className="mt-1 block w-full px-3 py-2 border border-line rounded-md shadow-sm" onChange={handleChange} />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink">Email</label>
              <input type="email" name="email" required className="mt-1 block w-full px-3 py-2 border border-line rounded-md shadow-sm" onChange={handleChange} />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink">Password</label>
              <input type="password" name="password" required className="mt-1 block w-full px-3 py-2 border border-line rounded-md shadow-sm" onChange={handleChange} />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ink">Branch</label>
                <input type="text" name="branch" required className="mt-1 block w-full px-3 py-2 border border-line rounded-md shadow-sm" onChange={handleChange} />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink">CGPA</label>
                <input type="number" step="0.01" name="cgpa" required className="mt-1 block w-full px-3 py-2 border border-line rounded-md shadow-sm" onChange={handleChange} />
              </div>
            </div>

            <div className="pt-2">
              <button type="submit" className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-saffron hover:bg-saffron-deep">
                Sign up
              </button>
            </div>
          </form>
          
          <div className="mt-6 text-center">
            <Link to="/student/login" className="text-sm font-medium text-navy">Already have an account? Log in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
