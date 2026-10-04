import { createContext, useContext, useEffect, useState } from 'react'
import { getMe, setAccessToken } from '../api/student'
import { revokeSessions } from '../api/accountData'

const AuthContext = createContext(null)
const TOKEN_KEY = 'jobjugaad-session'
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    let active = true
    const token = sessionStorage.getItem(TOKEN_KEY)
    if (!token) { setLoading(false); return }
    setAccessToken(token)
    getMe().then((value) => { if (active) setUser(value) })
      .catch(() => { if (active) { sessionStorage.removeItem(TOKEN_KEY); setAccessToken(null) } })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])
  function authenticate(result) {
    sessionStorage.setItem(TOKEN_KEY, result.access_token)
    setAccessToken(result.access_token)
    setUser(result.user)
  }
  async function refreshUser() { const current = await getMe(); setUser(current); return current }
  async function logout(localOnly = false) {
    if (localOnly !== true && sessionStorage.getItem(TOKEN_KEY)) await revokeSessions()
    sessionStorage.removeItem(TOKEN_KEY)
    setAccessToken(null)
    setUser(null)
  }
  return <AuthContext.Provider value={{ user, loading, authenticate, logout, refreshUser }}>{children}</AuthContext.Provider>
}
export const useAuth = () => useContext(AuthContext)
