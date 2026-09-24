import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authPath, roleHome } from '../context/roleHome'

// AuthProvider restores the session through /auth/me, which verifies the JWT server-side.
// The selected login card never grants a role. API authorization remains mandatory.
export function RoleGate({ user, loading, role, children }) {
  if (loading) return <p role="status">Checking your session…</p>
  if (!user) return <Navigate to={authPath(role)} replace />
  if (user.role !== role) return <Navigate to={roleHome(user.role)} replace />
  return children
}
export default function RoleGuard({ role, children }) {
  return <RoleGate {...useAuth()} role={role}>{children}</RoleGate>
}
