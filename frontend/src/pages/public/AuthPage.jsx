import { Link, Navigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authPath, roleHome, validRole } from '../../context/roleHome'
import { portals, PortalIcon } from '../../components/PortalIdentity'
import mascot from '../../assets/brand/mascot.png'
import AuthForm from './AuthForm'

export function RoleSelection({ mode = 'login' }) {
  return <div className="mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-20">
    <div className="mx-auto max-w-2xl text-center"><p className="text-xs font-bold uppercase tracking-[0.18em] text-saffron-deep">01 Choose your role · 02 Sign in</p><h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-navy sm:text-5xl">Your journey. Your portal.</h1><p className="mt-5 text-lg leading-7 text-muted">Tell us where you fit in.<br />We’ll take you to the right place.</p></div>
    <div className="mt-12 grid gap-5 lg:grid-cols-3">{portals.map(p => <Link key={p.role} to={authPath(p.role, mode)} className="group flex flex-col rounded-3xl border border-line bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:border-navy/35 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-navy motion-reduce:transform-none motion-reduce:transition-none">
      <div className="flex items-center justify-between"><span className={`inline-flex rounded-2xl p-4 ${p.tone}`}><PortalIcon role={p.role} className="h-8 w-8" /></span><span aria-hidden="true" className="text-xl text-muted transition group-hover:translate-x-1 motion-reduce:transform-none">↗</span></div>
      <p className="mt-8 text-[10px] font-bold uppercase tracking-[0.16em] text-muted">{p.eyebrow}</p><h2 className="mt-2 text-3xl font-bold text-navy">{p.label}</h2><p className="mt-2 text-sm font-semibold text-navy">{p.name}</p><p className="mb-8 mt-4 text-sm leading-6 text-muted">{p.line}</p>
      <span className="mt-auto border-t border-line pt-5 text-sm font-bold text-navy">Continue as {p.label} <span aria-hidden="true" className="float-right">→</span></span>
    </Link>)}</div>
    <div className="mx-auto mt-10 flex max-w-xl items-center justify-center gap-5 rounded-2xl border border-line bg-white p-5"><img src={mascot} alt="" width="705" height="525" className="h-auto w-20 shrink-0 rounded-lg" /><div><p className="text-sm font-semibold text-navy">Naya account? Welcome aboard.</p><p className="mt-1 text-xs leading-5 text-muted">Students and recruiters can sign up on the next screen. Admin access is provided by your placement team.</p></div></div>
    <p className="mt-7 text-center text-sm"><Link to="/" className="rounded text-muted underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-navy">← Back to JobJugaad</Link></p>
  </div>
}
export function RoleAuthScreen({ role, signup, onAuthenticated }) {
  const portal = portals.find(p => p.role === role)
  const creating = signup && role !== 'admin'
  return <div className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
    <Link to="/auth" className="inline-block rounded text-sm font-semibold text-navy underline underline-offset-4 focus-visible:outline-2">← Choose a different role</Link>
    <div className="mt-6 grid overflow-hidden rounded-3xl border border-line bg-white shadow-sm lg:grid-cols-[0.85fr_1.15fr]">
      <section className="flex flex-col bg-navy-dark p-8 text-white sm:p-10"><span className="inline-flex w-fit rounded-2xl bg-white/10 p-4 text-saffron"><PortalIcon role={role} /></span><p className="mt-8 text-xs font-bold uppercase tracking-widest text-saffron">{portal.label} · {portal.name}</p><h1 className="mt-4 text-3xl font-bold leading-tight">{portal.line}</h1><p className="mt-5 text-sm leading-7 text-white/80">{portal.description}</p><div className="mt-8 hidden overflow-hidden rounded-2xl bg-white lg:block"><img src={mascot} width="705" height="525" alt="The JobJugaad mascot with a laptop" className="h-auto w-full" /></div><p className="mt-6 text-xs text-white/70">Explainability-first. Your next step, with a clear why.</p></section>
      <section className="p-8 sm:p-10"><p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">02 {creating ? 'Create your account' : 'Welcome back'}</p><h2 className="mt-3 text-2xl font-bold text-navy">{portal.label} {creating ? 'signup' : 'login'}</h2>
        {role !== 'admin' ? <nav aria-label="Account action" className="mt-6 grid grid-cols-2 gap-1 rounded-xl bg-paper p-1">{[['login', 'Log in'], ['signup', 'Sign up']].map(([mode, label]) => <Link key={mode} to={authPath(role, mode)} aria-current={(mode === 'signup') === creating ? 'page' : undefined} className={`rounded-lg px-4 py-2.5 text-center text-sm font-bold focus-visible:outline-2 focus-visible:outline-navy ${(mode === 'signup') === creating ? 'bg-navy text-white' : 'text-muted hover:text-navy'}`}>{label}</Link>)}</nav> : <p className="mt-4 rounded-xl bg-paper p-3 text-sm text-muted">Sign in with your authorized college admin account. Public admin signup is not available.</p>}
        <p className="mt-5 text-xs leading-5 text-muted">Public hackathon demo · use synthetic details.{creating && role === 'recruiter' ? ' Company identity is not verified.' : ''}</p>
        <AuthForm key={`${role}-${creating}`} role={role} signup={creating} onAuthenticated={onAuthenticated} />
      </section>
    </div>
  </div>
}
export default function AuthPage() {
  const { user, authenticate } = useAuth()
  const [params] = useSearchParams()
  if (user) return <Navigate to={roleHome(user.role)} replace />
  const role = validRole(params.get('role'))
  const mode = params.get('mode') === 'signup' ? 'signup' : 'login'
  return role ? <RoleAuthScreen role={role} signup={mode === 'signup'} onAuthenticated={authenticate} /> : <RoleSelection mode={mode} />
}
