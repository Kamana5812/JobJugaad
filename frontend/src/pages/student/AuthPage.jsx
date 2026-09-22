import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import posterLogo from '../../../../assets/logo_poster.png'
import { logIn, signUp, errorMessage } from '../../api/student'
import { useAuth } from '../../context/AuthContext'
import { FormField, buttonStyle, Message } from '../../components/FormField'

export default function AuthPage({ signup = false }) {
  const { user, authenticate } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', college_id: 1 })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to={user.role === "recruiter" ? "/recruiter" : "/student/profile"} replace />
  const change = (key) => (event) => setForm({ ...form, [key]: event.target.value })
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true)
    try {
      const input = { email: form.email, password: form.password, college_id: Number(form.college_id) }
      const result = signup ? await signUp({ ...input, name: form.name }) : await logIn(input)
      authenticate(result); navigate(result.user.role === 'recruiter' ? '/recruiter' : '/student/profile', { replace: true })
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <div className="grid overflow-hidden rounded-3xl border border-line bg-white shadow-sm lg:grid-cols-2">
    <section className="bg-navy-dark p-8 text-white sm:p-12">
      <img src={posterLogo} alt="JobJugaad JJ graduation mark" className="h-28 w-28 rounded-2xl bg-white" />
      <p className="mt-8 text-xs font-bold uppercase tracking-widest text-saffron">Explainability-first · Career Copilot</p>
      <h1 className="mt-4 text-4xl font-bold leading-tight">{signup ? 'Your next chapter starts with clarity.' : 'Welcome back. Agla jugaad?'}</h1>
      <p className="mt-5 leading-7 text-white/80">Build your profile. See where each readiness point comes from. Choose your next step with a clear why.</p>
      <p className="mt-8 text-sm text-white/70">A weighted rule you can inspect. No hidden placement prediction.</p>
    </section>
    <section className="p-8 sm:p-12">
      <h2 className="text-2xl font-bold text-navy">{signup ? 'Create your student account' : 'Log in to JobJugaad'}</h2>
      <p className="mt-2 text-sm text-muted">Public hackathon demo · use synthetic details.</p>
      <form className="mt-6 space-y-5" onSubmit={submit}>
        {signup && <FormField label="Full name" autoComplete="name" required maxLength="100" value={form.name} onChange={change('name')} />}
        <FormField label="Email" type="email" autoComplete="email" required maxLength="254" value={form.email} onChange={change('email')} />
        <FormField label="Password" type="password" autoComplete={signup ? 'new-password' : 'current-password'} required minLength="10" maxLength="72"
          hint={signup ? '10 or more characters, up to 72 UTF-8 bytes.' : undefined} value={form.password} onChange={change('password')} />
        <FormField label="Demo college" value={form.college_id} onChange={change('college_id')} hint="Choose the same college at every login. Demo enrollment is self-selected; real college affiliation is not verified.">
          <option value="1">Demo College 1</option><option value="2">Demo College 2</option>
        </FormField>
        <Message error>{error}</Message>
        <button className={buttonStyle + ' w-full'} disabled={busy}>{busy ? 'Connecting…' : signup ? 'Create account' : 'Log in'}</button>
      </form>
      <p className="mt-6 text-sm text-muted">{signup ? 'Already have an account? ' : 'New here? '}
        <Link className="font-bold text-navy underline underline-offset-4" to={signup ? '/login' : '/signup'}>{signup ? 'Log in' : 'Create an account'}</Link></p>
    <p className="mt-4 text-sm"><Link className="font-bold text-navy underline" to="/recruiter/signup">Recruiting? Create a Talent Finder account</Link></p>
    </section>
  </div>
}
