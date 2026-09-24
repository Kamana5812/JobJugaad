import { Link } from 'react-router-dom'
import hero from '../../assets/hero/landing-journey.png'
import { buttonStyle } from '../../components/FormField'
import { portals, PortalIcon } from '../../components/PortalIdentity'
import { authPath } from '../../context/roleHome'
import MatchingExample from './MatchingExample'

const SectionTitle = ({ number, children }) => <p className="text-xs font-bold uppercase tracking-[0.18em] text-muted"><span className="mr-3 text-saffron-deep">{number}</span>{children}</p>
export default function LandingPage() {
  return <>
    <section className="border-b border-line bg-paper px-5 pt-12 sm:px-8 sm:pt-16">
      <div className="mx-auto max-w-7xl text-center"><p className="inline-flex items-center gap-2 rounded-full border border-line bg-white px-4 py-2 text-[11px] font-bold uppercase tracking-[0.13em] text-navy"><span aria-hidden="true" className="h-2 w-2 rounded-full bg-growth" />Explainability-first campus placement</p>
        <h1 className="mx-auto mt-6 max-w-4xl text-4xl font-bold leading-[1.08] tracking-tight text-navy sm:text-6xl lg:text-7xl">Placement ka Jugaad,<br /><span className="text-saffron-deep">AI ke Saath.</span></h1>
        <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-muted sm:text-lg">From campus to career—with a clear why behind every score, shortlist, and next step.</p>
        <div className="mt-7 flex flex-wrap items-center justify-center gap-5"><Link to="/auth" className={buttonStyle + ' px-8'}>Get Started <span aria-hidden="true" className="ml-3">→</span></Link><a href="#portals" className="rounded py-3 text-sm font-semibold text-navy hover:underline focus-visible:outline-2">Find your portal ↓</a></div>
        <p className="mt-4 text-xs text-muted">Rules explain readiness & matching. Optional placement models are separate.</p>
        <img src={hero} alt="The JobJugaad mascot moves from scattered spreadsheets and messages toward a clear six-factor readiness card." width="1774" height="887" fetchPriority="high" className="mx-auto mt-8 h-auto w-full max-w-5xl rounded-t-3xl" />
      </div>
    </section>
    <section className="mx-auto max-w-7xl px-5 py-16 sm:px-8 lg:py-24">
      <SectionTitle number="01">Less chasing. More clarity.</SectionTitle>
      <div className="mt-6 grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-center">
        <div><h2 className="text-3xl font-bold leading-tight tracking-tight text-navy sm:text-4xl">Your placement journey<br />deserves a clearer path.</h2><p className="mt-5 max-w-lg leading-7 text-muted">Profiles in one sheet. Shortlists in another. Interview updates buried in a chat. Bring the next step—and the reason for it—into one shared workflow.</p></div>
        <div className="grid gap-4 sm:grid-cols-2"><div className="rounded-2xl border border-line bg-white p-6"><p className="text-xs font-bold uppercase tracking-widest text-muted">Before · scattered</p><h3 className="mt-5 text-lg font-bold text-navy">“Which sheet is final?”</h3><ul className="mt-5 space-y-4 text-sm text-muted">{['Disconnected student profiles', 'Shortlists without a clear reason', 'Conflicting interview slots'].map(t => <li key={t} className="flex gap-3"><span aria-hidden="true">↔</span>{t}</li>)}</ul></div>
          <div className="rounded-2xl border border-growth/25 bg-growth-soft p-6"><p className="text-xs font-bold uppercase tracking-widest text-navy">After · connected</p><h3 className="mt-5 text-lg font-bold text-navy">“Here’s your next step.”</h3><ul className="mt-5 space-y-4 text-sm text-navy">{['A structured profile you can review', 'Every factor, gap, and explanation', 'Conflict checks before approval'].map(t => <li key={t} className="flex gap-3"><span aria-hidden="true" className="font-bold">✓</span>{t}</li>)}</ul></div></div>
      </div>
    </section>
    <section id="portals" className="scroll-mt-6 border-y border-line bg-white px-5 py-16 sm:px-8 lg:py-24"><div className="mx-auto max-w-7xl">
      <SectionTitle number="02">One journey. Three perspectives.</SectionTitle><div className="mt-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><h2 className="text-3xl font-bold tracking-tight text-navy sm:text-4xl">Find your kind of Jugaad.</h2><p className="max-w-sm text-sm leading-6 text-muted">A dedicated space for every person<br className="hidden sm:block" /> moving campus placements forward.</p></div>
      <div className="mt-10 grid gap-5 lg:grid-cols-3">{portals.map(p => <article key={p.role} className="flex flex-col rounded-3xl border border-line bg-paper p-7 transition hover:border-navy/25">
        <div className="flex items-center justify-between"><span className={`inline-flex rounded-2xl p-4 ${p.tone}`}><PortalIcon role={p.role} /></span><span className="text-xs font-semibold text-muted">For {p.role === 'admin' ? 'placement teams' : p.role + 's'}</span></div>
        <h3 className="mt-6 text-2xl font-bold leading-tight text-navy">{p.name}</h3><p className="mt-3 text-sm leading-6 text-muted">{p.description}</p><ul className="mb-7 mt-5 space-y-2 text-sm text-navy">{p.features.map(item => <li key={item}><span aria-hidden="true" className="mr-2 text-growth">✓</span>{item}</li>)}</ul>
        <Link to={authPath(p.role)} className="mt-auto flex items-center justify-between rounded-lg border-t border-line pt-5 text-sm font-bold text-navy hover:underline focus-visible:outline-2">Sign in as {p.label}<span aria-hidden="true">→</span></Link>
      </article>)}</div>
    </div></section>
    <section id="explainability" className="mx-auto grid max-w-7xl scroll-mt-6 gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16 lg:py-24">
      <div><SectionTitle number="03">How it explains itself</SectionTitle><h2 className="mt-6 text-3xl font-bold leading-tight tracking-tight text-navy sm:text-4xl">A score starts<br />the conversation.<br /><span className="text-saffron-deep">The why moves it forward.</span></h2>
        <p className="mt-6 leading-7 text-muted">A frontend-focused student can meet the academic requirement and still need Python for a backend role. JobJugaad names the gap, shows the calculation, and suggests a practical next step.</p>
        <ol className="mt-8 space-y-5 text-sm text-navy">{['Inspect every contributing factor.', 'Understand the specific requirements.', 'Let a person make the final decision.'].map((t, i) => <li key={t} className="flex items-center gap-4"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line bg-white font-bold text-saffron-deep">{i + 1}</span>{t}</li>)}</ol>
        <p className="mt-8 text-xs leading-6 text-muted">Matching uses exact skill keywords and a proposed weighted rule. Its weights are assumptions, not empirically validated hiring criteria. Recruiter overrides are recorded for review.</p>
      </div><MatchingExample />
    </section>
    <section className="border-t border-line bg-warning-soft px-5 py-14 text-center sm:px-8"><p className="text-xs font-bold uppercase tracking-widest text-navy">Your Next Jugaad</p><h2 className="mt-3 text-3xl font-bold text-navy">Start with a little more clarity.</h2><p className="mt-3 text-muted">Pick your role. Find your next step.</p><Link to="/auth" className={buttonStyle + ' mt-6'}>Let’s get started →</Link></section>
  </>
}
