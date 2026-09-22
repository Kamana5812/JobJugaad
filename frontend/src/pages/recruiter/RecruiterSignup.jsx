import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import posterLogo from '../../../../assets/logo_poster.png'
import { recruiterSignup } from '../../api/recruiter'
import { errorMessage } from '../../api/student'
import { useAuth } from '../../context/AuthContext'
import { FormField, buttonStyle, Message } from '../../components/FormField'

export default function RecruiterSignup() {
  const { user, authenticate } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', industry: '', email: '', password: '', college_id: '1' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to={user.role === 'recruiter' ? '/recruiter' : '/student/profile'} replace />
  const change = key => event => setForm({ ...form, [key]: event.target.value })
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const result = await recruiterSignup({ email: form.email, password: form.password, college_id: Number(form.college_id),
        company: { name: form.name, industry: form.industry } })
      authenticate(result); navigate('/recruiter', { replace: true })
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <div className="grid overflow-hidden rounded-3xl border border-line bg-white shadow-sm lg:grid-cols-2">
    <section className="bg-navy-dark p-8 text-white sm:p-12">
      <img src={posterLogo} alt="JobJugaad JJ graduation mark" className="h-28 w-28 rounded-2xl bg-white" />
      <p className="mt-8 text-xs font-bold uppercase tracking-widest text-saffron">Explainability-first · Talent Finder</p>
      <h1 className="mt-4 text-4xl font-bold leading-tight">Find the fit.<br />See the why.</h1>
      <p className="mt-5 text-white/80">Set your requirements. Review each contributing factor. Make the final shortlist decision with a recorded reason.</p>
      <p className="mt-8 text-sm text-white/70">Keyword matching and weighted rules. Every recommendation stays open to human review.</p>
    </section>
    <section className="p-8 sm:p-12">
      <h2 className="text-2xl font-bold text-navy">Create a recruiter account</h2>
      <p className="mt-2 text-sm text-muted">Public hackathon demo · use synthetic details. College affiliation and company identity are not verified.</p>
      <form onSubmit={submit} className="mt-6 space-y-4">
        <FormField label="Company name" required maxLength="160" value={form.name} onChange={change('name')} />
        <FormField label="Industry" required maxLength="100" value={form.industry} onChange={change('industry')} />
        <FormField label="Email" type="email" autoComplete="email" required maxLength="254" value={form.email} onChange={change('email')} />
        <FormField label="Password" type="password" autoComplete="new-password" required minLength="10" maxLength="72" hint="At least 10 characters; maximum 72 UTF-8 bytes." value={form.password} onChange={change('password')} />
        <FormField label="Demo college" value={form.college_id} onChange={change('college_id')} hint="College 1 contains the synthetic demo population. Use the same college when logging in.">
          <option value="1">Demo College 1</option><option value="2">Demo College 2</option>
        </FormField>
        <Message error>{error}</Message>
        <button disabled={busy} className={buttonStyle + ' w-full'}>{busy ? 'Creating account…' : 'Create recruiter account'}</button>
      </form>
      <p className="mt-5 text-sm"><Link to="/login" className="font-bold text-navy underline">Already registered? Log in</Link></p>
    </section>
  </div>
}
