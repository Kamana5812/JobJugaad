import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import CollegeSelector from '../../components/CollegeSelector'
import { FormField, Message, buttonStyle } from '../../components/FormField'
import { requestPasswordReset } from '../../api/passwordRecovery'
import { errorMessage } from '../../api/student'

export default function ForgotPasswordPage() {
  const [query] = useSearchParams()
  const [college, setCollege] = useState(query.get('college_id') || '10219')
  const [legacy, setLegacy] = useState(['1', '2'].includes(college))
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault(); setError(''); setMessage(''); setBusy(true)
    try { setMessage((await requestPasswordReset({ email, college_id: Number(college) })).detail) }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section className="mx-auto max-w-lg rounded-2xl border border-line bg-white p-6 sm:p-8">
    <h1 className="text-2xl font-bold text-navy">Recover your account</h1>
    <p className="mt-2 text-sm text-muted">Use your registered email and the college selected when you created your account.</p>
    <form onSubmit={submit} className="mt-6 space-y-5">
      <FormField label="Registered email" type="email" autoComplete="email" required maxLength="254" value={email} onChange={e => setEmail(e.target.value)} disabled={busy} />
      <CollegeSelector allowDemo={legacy} value={college} onChange={e => setCollege(e.target.value)} disabled={busy} />
      <details className="text-xs text-muted"><summary>Existing demonstration account</summary><label className="mt-2 flex gap-2"><input type="checkbox" checked={legacy} disabled={busy} onChange={e => { setLegacy(e.target.checked); setCollege(e.target.checked ? '1' : '10219') }} />Access archived demo colleges</label></details>
      <Message error>{error}</Message><Message>{message}</Message>
      <button className={buttonStyle + ' w-full'} disabled={busy}>{busy ? 'Requesting…' : 'Send reset link'}</button>
    </form>
    <Link className="mt-5 inline-block text-sm text-navy underline" to="/auth">Back to sign in</Link>
  </section>
}
