import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Login from './pages/student/Login';
import Signup from './pages/student/Signup';
import Dashboard from './pages/student/Dashboard';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/student/login" replace />} />
          <Route path="/student/login" element={<Login />} />
          <Route path="/student/signup" element={<Signup />} />
          <Route path="/student/dashboard" element={<Dashboard />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
