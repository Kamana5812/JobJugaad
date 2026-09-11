import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import SignupPage from "./pages/SignupPage";
import LoginPage from "./pages/LoginPage";
import StudentProfile from "./pages/StudentProfile";
import RecruiterDashboard from "./pages/RecruiterDashboard";


function PrivateRoute({ children }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <StudentProfile />
              </PrivateRoute>
            }
          />
          {/* Default redirect */}
          <Route path="/recruiter/dashboard" element={<PrivateRoute><RecruiterDashboard /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
