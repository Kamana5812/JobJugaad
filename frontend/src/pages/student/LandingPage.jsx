import { Link } from 'react-router-dom'
import posterLogo from '../../../../assets/logo_poster.png'
import HealthStatus from '../../components/HealthStatus'
import { buttonStyle, secondaryStyle } from '../../components/FormField'

export default function LandingPage() {
  return <div className="space-y-10">
    <section className="grid items-center gap-8 rounded-3xl bg-navy-dark p-8 sm:p-12 lg:grid-cols-[1.5fr_1fr]">
      <div><p className="text-xs font-bold uppercase tracking-[0.2em] text-saffron">Explainability-first campus placement</p>
        <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">Placement ka Jugaad.<br /><span className="text-saffron">With a clear why.</span></h1>
        <p className="mt-5 max-w-xl leading-7 text-white/80">Turn your profile into a transparent readiness view, or create a recruiter drive and inspect an explained shortlist. See every contributing factor, understand the gaps, and plan your next step.</p>
        <div className="mt-8 flex flex-wrap gap-3"><Link to="/signup" className={buttonStyle}>Build my profile →</Link><Link to="/login" className={secondaryStyle + ' inline-flex items-center'}>Log in</Link><Link to="/recruiter/signup" className={secondaryStyle + ' inline-flex items-center'}>Talent Finder →</Link></div>
        <p className="mt-5 text-xs text-white/60">Public hackathon prototype · use synthetic details</p>
      </div>
      <div className="mx-auto w-full max-w-64 rounded-2xl border border-line bg-white p-5"><img src={posterLogo} alt="JobJugaad graduation cap and upward arrow" width="1254" height="1254" className="h-auto w-full" /></div>
    </section>
    <div className="grid gap-8 lg:grid-cols-2"><section>
      <h2 className="text-2xl font-bold text-navy"><span className="mr-3 text-saffron">01</span>Know the why. Find your next step.</h2>
      <p className="mt-4 leading-7 text-muted">Add your skills, projects, academics, and existing assessment results. Career Copilot shows exactly how the proposed weighted rule calculates your readiness.</p>
      <p className="mt-4 leading-7 text-muted">Resume upload extracts text for your review. No hidden hiring predictions, and no claim of measured accuracy.</p>
      <p className="mt-6 font-semibold text-navy">Reject less → Identify the gap → Help improve</p>
    </section><HealthStatus /></div>
  </div>
}
