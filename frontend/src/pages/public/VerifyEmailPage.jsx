import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { verifyEmail } from '../../api/accounts'
import { errorMessage } from '../../api/student'
import { Message } from '../../components/FormField'

export default function VerifyEmailPage() {
  const [input] = useState(() => { const p = new URLSearchParams(window.location.hash.slice(1)); return { college_id: Number(p.get('college_id')), token: p.get('token') || '' } })
  const [message, setMessage] = useState('Checking your verification link…')
  const [error, setError] = useState(false)
  useEffect(() => {
    window.history.replaceState(null, '', '/verify-email')
    let active = true
    if (!input.token || !input.college_id) { setError(true); setMessage('This verification link is incomplete. Sign in and request a new email.'); return }
    verifyEmail(input).then(r => { if (active) setMessage(r.detail) }).catch(e => { if (active) { setError(true); setMessage(errorMessage(e)) } })
    return () => { active = false }
  }, [input])
  return <div className="mx-auto max-w-xl space-y-5 rounded-xl border border-line bg-white p-8"><h1 className="text-2xl font-semibold text-navy">Email verification</h1><Message error={error}>{message}</Message><p className="text-sm text-muted">Verification confirms access to your inbox. College affiliation still requires an administrator’s review.</p><Link to="/auth" className="font-semibold text-navy underline">Continue to your account →</Link></div>
}
