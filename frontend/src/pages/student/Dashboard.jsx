import { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import { Upload, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react';

export default function Dashboard() {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate('/student/login');
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      const profileRes = await api.get(`/students/${user.user_id}/profile`);
      setProfile(profileRes.data);
      const readinessRes = await api.get(`/students/${user.user_id}/readiness`);
      setReadiness(readinessRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      await api.post(`/students/${user.user_id}/resume`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchData();
    } catch (e) {
      console.error(e);
      alert('Failed to upload resume.');
    } finally {
      setUploading(false);
      setFile(null);
    }
  };

  const getBandColor = (band) => {
    switch (band) {
      case 'Highly Employable': return 'text-green-subtle bg-green-100';
      case 'Ready': return 'text-green-subtle bg-green-100';
      case 'Developing': return 'text-saffron-deep bg-saffron-100';
      case 'Not Ready': return 'text-red-600 bg-red-100';
      default: return 'text-muted bg-paper';
    }
  };

  if (!profile || !readiness) return <div className="p-8 text-navy font-semibold text-center mt-20">Loading profile data...</div>;

  return (
    <div className="min-h-screen bg-paper">
      {/* Navbar */}
      <nav className="bg-navy p-4 flex justify-between items-center text-white">
        <h1 className="text-xl font-bold">JobJugaad</h1>
        <button onClick={logout} className="text-sm font-medium hover:text-saffron transition-colors">Logout</button>
      </nav>

      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Col: Profile & Resume */}
        <div className="md:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-line">
            <h2 className="text-xs font-bold text-muted uppercase tracking-wider mb-4">Profile</h2>
            <h3 className="text-2xl font-bold text-navy mb-1">{profile.name}</h3>
            <p className="text-ink mb-1">{profile.branch} | CGPA: {profile.cgpa}</p>
            <p className="text-muted text-sm">{profile.resume_text ? 'Resume Uploaded ✓' : 'No Resume Uploaded'}</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-line">
            <h2 className="text-xs font-bold text-muted uppercase tracking-wider mb-4">Upload Resume</h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} className="block w-full text-sm text-ink file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-navy file:text-white hover:file:bg-navy-dark transition-colors cursor-pointer" />
              <button type="submit" disabled={!file || uploading} className="w-full flex justify-center py-2 px-4 border border-transparent rounded shadow-sm text-sm font-medium text-white bg-saffron hover:bg-saffron-deep disabled:opacity-50 transition-colors">
                {uploading ? 'Processing PDF...' : 'Upload & Parse Resume'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Col: Readiness Score */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-line">
            <h2 className="text-xs font-bold text-muted uppercase tracking-wider mb-4">Kitne Ready Ho? (Readiness)</h2>
            <div className="flex items-center gap-6 mb-6">
              <div className="text-6xl font-bold text-navy">{readiness.score}</div>
              <div>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${getBandColor(readiness.band)}`}>
                  {readiness.band}
                </span>
              </div>
            </div>
            
            <div className="p-4 bg-paper rounded-lg border border-line mb-6">
              <p className="text-ink font-semibold mb-1">Why did I get this score?</p>
              <p className="text-muted text-sm">{readiness.explanation}</p>
            </div>

            <h3 className="text-md font-bold text-navy mb-3">Factor Breakdown</h3>
            <div className="overflow-x-auto rounded border border-line">
              <table className="min-w-full divide-y divide-line">
                <thead className="bg-paper">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-muted uppercase tracking-wider">Factor</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-muted uppercase tracking-wider">Score Contribution</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-line">
                  {Object.entries(readiness.breakdown).map(([factor, score]) => (
                    <tr key={factor} className="hover:bg-gray-50">
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-ink flex items-center gap-3">
                        {score >= 80 ? <CheckCircle className="w-4 h-4 text-green-subtle" /> : score >= 50 ? <AlertCircle className="w-4 h-4 text-saffron" /> : <AlertTriangle className="w-4 h-4 text-red-500" />}
                        {factor}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-muted text-right">{score}/100</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
