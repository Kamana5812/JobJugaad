import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Login from './pages/student/Login';
import Signup from './pages/student/Signup';
import StudentDashboard from './pages/student/Dashboard';
import RecruiterDashboard from './pages/recruiter/Dashboard';
import DriveDetails from './pages/recruiter/DriveDetails';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/student/login" replace />} />
          <Route path="/student/login" element={<Login />} />
          <Route path="/student/signup" element={<Signup />} />
          <Route path="/student/dashboard" element={<StudentDashboard />} />
          <Route path="/recruiter/dashboard" element={<RecruiterDashboard />} />
          <Route path="/recruiter/drives/:id" element={<DriveDetails />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
