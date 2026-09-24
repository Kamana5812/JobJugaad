import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage } from '../../api/student'
import { authenticateAccount } from '../../api/authentication'
import { roleHome } from '../../context/roleHome'
import { FormField, buttonStyle, Message } from '../../components/FormField'

export default function AuthForm({ role, signup, onAuthenticated }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', industry: '', email: '', password: '', college_id: '1' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const creating = signup && role !== 'admin'
  const change = key => event => setForm(current => ({ ...current, [key]: event.target.value }))
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      const result = await authenticateAccount(role, creating, form)
      // Only the authenticated server role chooses the destination, never the role card.
      onAuthenticated(result); navigate(roleHome(result.user.role), { replace: true })
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <form onSubmit={submit} className="mt-6 space-y-5" aria-label={`${role} ${creating ? 'signup' : 'login'}`}>
    {creating && <FormField label={role === 'recruiter' ? 'Company name' : 'Full name'} autoComplete={role === 'recruiter' ? 'organization' : 'name'} required maxLength={role === 'recruiter' ? 160 : 100} value={form.name} onChange={change('name')} disabled={busy} />}
    {creating && role === 'recruiter' && <FormField label="Industry" required maxLength="100" value={form.industry} onChange={change('industry')} disabled={busy} />}
    <FormField label="Email" type="email" autoComplete="email" required maxLength="254" value={form.email} onChange={change('email')} disabled={busy} />
    <FormField label="Password" type="password" autoComplete={creating ? 'new-password' : 'current-password'} required minLength="10" maxLength="72" hint={creating ? 'At least 10 characters; up to 72 UTF-8 bytes.' : undefined} value={form.password} onChange={change('password')} disabled={busy} />
    <FormField label="Demo college" value={form.college_id} onChange={change('college_id')} disabled={busy} hint="Choose the same college each time you sign in. Demo enrollment is self-selected; college affiliation is not verified."><option value="1">Demo College 1</option><option value="2">Demo College 2</option></FormField>
    <Message error>{error}</Message>
    <button disabled={busy} className={buttonStyle + ' w-full'}>{busy ? 'Connecting…' : creating ? `Create ${role} account` : `Sign in as ${role}`}</button>
    <p className="text-xs leading-5 text-muted">Your account’s verified role determines which portal opens. Choosing a card does not change your access.</p>
  </form>
}
