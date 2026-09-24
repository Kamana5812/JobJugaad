import { lazy, Suspense, useEffect } from 'react'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import LandingPage from './pages/public/LandingPage'
import AuthPage from './pages/public/AuthPage'
import ProfilePage from './pages/student/ProfilePage'
import OffersPage from './pages/student/OffersPage'
import NotificationsPage from './components/NotificationsPage'
import TalentPage from './pages/recruiter/TalentPage'
import RoleGuard from './components/RoleGuard'
import SiteHeader from './components/SiteHeader'
import SiteFooter from './components/SiteFooter'
const AdminPage = lazy(() => import('./pages/admin/AdminPage'))

function PageFocus() {
  const { pathname, search, hash } = useLocation()
  useEffect(() => {
    const titles = { '/': 'Placement ka Jugaad', '/auth': 'Choose your portal', '/student': 'Career Copilot', '/recruiter': 'Talent Finder', '/admin': 'Placement Command Center' }
    document.title = `JobJugaad | ${titles[pathname] || 'Campus placement'}`
    if (!hash) { window.scrollTo(0, 0); document.getElementById('main')?.focus({ preventScroll: true }) }
  }, [pathname, search, hash])
  return null
}
export function AppRoutes() {
  const { user } = useAuth()
  return <Routes>
    <Route path="/" element={<LandingPage />} /><Route path="/auth" element={<AuthPage />} />
    <Route path="/login" element={<Navigate to="/auth" replace />} /><Route path="/signup" element={<Navigate to="/auth?mode=signup" replace />} />
    <Route path="/recruiter/login" element={<Navigate to="/auth?role=recruiter&mode=login" replace />} />
    <Route path="/recruiter/signup" element={<Navigate to="/auth?role=recruiter&mode=signup" replace />} />
    <Route path="/student" element={<RoleGuard role="student"><ProfilePage /></RoleGuard>} />
    <Route path="/student/profile" element={<Navigate to="/student" replace />} />
    <Route path="/student/offers" element={<RoleGuard role="student"><OffersPage /></RoleGuard>} />
    <Route path="/notifications" element={user ? <NotificationsPage /> : <Navigate to="/auth" replace />} />
    <Route path="/recruiter" element={<RoleGuard role="recruiter"><TalentPage /></RoleGuard>} />
    <Route path="/admin" element={<RoleGuard role="admin"><Suspense fallback={<p role="status">Loading Command Center…</p>}><AdminPage /></Suspense></RoleGuard>} />
    <Route path="*" element={<div className="rounded-2xl bg-white p-8"><h1 className="text-2xl font-bold text-navy">Page not found</h1><Link className="mt-4 inline-block underline" to="/">Back to JobJugaad</Link></div>} />
  </Routes>
}
function Layout() {
  const { user, loading, logout } = useAuth()
  const { pathname } = useLocation()
  const publicPage = ['/', '/auth', '/login', '/signup', '/recruiter/signup', '/recruiter/login'].includes(pathname)
  return <div className="min-h-screen bg-paper font-sans leading-relaxed text-ink">
    <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-10 focus:bg-white focus:p-4">Skip to content</a>
    <SiteHeader user={user} logout={logout} /><PageFocus />
    <main id="main" tabIndex="-1" className={publicPage ? 'outline-none' : 'mx-auto max-w-6xl px-5 py-8 outline-none sm:px-6 sm:py-12'}>
      {loading && pathname !== '/' ? <p role="status" className="px-5 py-16 text-center">Restoring your session…</p> : <AppRoutes />}
    </main><SiteFooter />
  </div>
}
export default function App() { return <AuthProvider><Layout /></AuthProvider> }
