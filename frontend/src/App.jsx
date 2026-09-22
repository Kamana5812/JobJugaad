import { Link, Navigate, Route, Routes } from 'react-router-dom'
import horizontalLogo from '../../assets/logo_horizontal.png'
import { AuthProvider, useAuth } from './context/AuthContext'
import LandingPage from './pages/student/LandingPage'
import AuthPage from './pages/student/AuthPage'
import ProfilePage from './pages/student/ProfilePage'
import RecruiterSignup from './pages/recruiter/RecruiterSignup'
import TalentPage from './pages/recruiter/TalentPage'
import { secondaryStyle } from './components/FormField'

function Layout() {
  const { user, loading, logout } = useAuth()
  return <div className="min-h-screen bg-paper font-sans leading-relaxed text-ink">
    <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-10 focus:bg-white focus:p-4">Skip to content</a>
    <header className="border-b border-line bg-white"><nav aria-label="Main navigation" className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-6">
      <Link to="/" aria-label="JobJugaad home"><img src={horizontalLogo} alt="JobJugaad — Placement ka Jugaad, AI ke Saath." width="1600" height="533" className="h-auto w-48 rounded-md sm:w-56" /></Link>
      <div className="flex items-center gap-4 text-sm font-semibold text-navy">{user ? <><Link to={user.role === "recruiter" ? "/recruiter" : "/student/profile"}>{user.role === "recruiter" ? "Talent Finder" : "My profile"}</Link><button onClick={logout} className={secondaryStyle}>Log out</button></>
        : <><Link to="/recruiter/signup">For recruiters</Link><Link to="/login">Log in</Link><Link to="/signup" className={secondaryStyle}>Get started</Link></>}</div>
    </nav></header>
    <main id="main" className="mx-auto max-w-6xl px-5 py-8 sm:px-6 sm:py-12">
      {loading ? <p role="status">Restoring your session…</p> : <Routes>
        <Route path="/" element={<LandingPage />} /><Route path="/signup" element={<AuthPage key="signup" signup />} />
        <Route path="/login" element={<AuthPage key="login" />} />
        <Route path="/student/profile" element={user?.role === "student" ? <ProfilePage /> : <Navigate to={user ? "/recruiter" : "/login"} replace />} />
        <Route path="/recruiter/signup" element={<RecruiterSignup />} />
        <Route path="/recruiter" element={user?.role === "recruiter" ? <TalentPage /> : <Navigate to={user ? "/student/profile" : "/login"} replace />} />
        <Route path="*" element={<div className="rounded-2xl bg-white p-8"><h1 className="text-2xl font-bold text-navy">Page not found</h1><Link className="mt-4 inline-block underline" to="/">Back to JobJugaad</Link></div>} />
      </Routes>}
    </main>
    <footer className="border-t border-line px-6 py-6 text-center text-xs text-muted">JobJugaad · Explainability-first CampusLink prototype · Career Copilot & Talent Finder</footer>
  </div>
}
export default function App() { return <AuthProvider><Layout /></AuthProvider> }
