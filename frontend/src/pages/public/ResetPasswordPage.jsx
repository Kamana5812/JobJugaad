import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FormField, Message, buttonStyle } from '../../components/FormField'
import { resetPassword } from '../../api/passwordRecovery'
import { errorMessage } from '../../api/student'
import { useAuth } from '../../context/AuthContext'

export default function ResetPasswordPage() {
  const { logout } = useAuth()
  const [link, setLink] = useState(() => {
    const fragment = new URLSearchParams(window.location.hash.slice(1))
    return { token: fragment.get('token') || '', college_id: Number(fragment.get('college_id')) }
  })
  useEffect(() => { window.history.replaceState(null, '', window.location.pathname) }, [])
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const valid = /^[A-Za-z0-9_-]{43}$/.test(link.token) && Number.isInteger(link.college_id) && link.college_id > 0
  async function submit(event) {
    event.preventDefault(); setError('')
    if (password !== confirmation) { setError('The passwords do not match.'); return }
    if (new TextEncoder().encode(password).length > 72) { setError('Use a password no longer than 72 UTF-8 bytes.'); return }
    setBusy(true)
    try {
      const result = await resetPassword({ ...link, password })
      await logout(true); setPassword(''); setConfirmation(''); setLink({ token: '', college_id: 0 }); setMessage(result.detail)
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section className="mx-auto max-w-lg rounded-2xl border border-line bg-white p-6 sm:p-8">
    <h1 className="text-2xl font-bold text-navy">Choose a new password</h1>
    <p className="mt-2 text-sm text-muted">Reset links expire after 30 minutes and can be used once. Resetting signs out your previous sessions.</p>
    <Message>{message}</Message>
    {!message && (valid ? <form onSubmit={submit} className="mt-6 space-y-5">
      <FormField label="New password" type="password" autoComplete="new-password" required minLength="10" maxLength="72" hint="At least 10 characters; up to 72 UTF-8 bytes." value={password} onChange={e => setPassword(e.target.value)} disabled={busy} />
      <FormField label="Confirm new password" type="password" autoComplete="new-password" required minLength="10" maxLength="72" value={confirmation} onChange={e => setConfirmation(e.target.value)} disabled={busy} />
      <Message error>{error}</Message>
      <button className={buttonStyle + ' w-full'} disabled={busy}>{busy ? 'Saving…' : 'Save new password'}</button>
    </form> : <p role="alert" className="mt-5 text-critical">Open the reset link from your email, or request a new link.</p>)}
    <div className="mt-5 flex gap-5 text-sm text-navy underline"><Link to="/auth">Sign in</Link><Link to="/forgot-password">Request a new link</Link></div>
  </section>
}
