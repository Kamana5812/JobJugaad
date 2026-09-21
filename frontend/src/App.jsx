import horizontalLogo from '../../assets/logo_horizontal.png'
import posterLogo from '../../assets/logo_poster.png'
import HealthStatus from './components/HealthStatus'

export default function App() {
  return (
    <div className="min-h-screen bg-paper font-sans leading-relaxed text-ink">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-10 focus:bg-white focus:p-4">Skip to content</a>
      <header className="border-b border-line bg-white">
        <nav aria-label="Main navigation" className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <a href="/" aria-label="JobJugaad home" className="rounded-lg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-navy">
            <img src={horizontalLogo} alt="JobJugaad — Placement ka Jugaad, AI ke Saath." className="h-auto w-56 rounded-md sm:w-64" width="1600" height="533" />
          </a>
          <span className="rounded-full border border-line px-4 py-2 text-xs font-semibold text-muted">BPUT Hackathon 2026 · CampusLink</span>
        </nav>
      </header>

      <main id="main" className="mx-auto max-w-6xl px-6 py-10 sm:py-16">
        <section className="grid items-center gap-8 rounded-3xl bg-navy-dark p-7 sm:p-12 lg:grid-cols-[1.5fr_1fr]" aria-labelledby="hero-heading">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-saffron">Explainability-first campus placement</p>
            <h1 id="hero-heading" className="mt-5 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl">Placement ka Jugaad.<br /><span className="text-saffron">With a clear why.</span></h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-white/80">A clearer path from campus to career — built around transparent, rule-based guidance and decisions people can review.</p>
            <p className="mt-7 inline-block rounded-full border border-white/20 px-4 py-2 text-xs font-medium text-white">Phase 0 · Environment &amp; Skeleton</p>
          </div>
          <div className="mx-auto w-full max-w-64 rounded-2xl border border-line bg-white p-5 shadow-sm">
            <img src={posterLogo} alt="JobJugaad JJ mark with a graduation cap and upward arrow" width="1254" height="1254" className="h-auto w-full" />
          </div>
        </section>

        <div className="mt-10 grid gap-8 lg:grid-cols-2">
          <section aria-labelledby="foundation-heading" className="py-3">
            <h2 id="foundation-heading" className="text-2xl font-bold text-navy"><span className="mr-3 text-saffron">01</span>The foundation comes first.</h2>
            <p className="mt-4 max-w-lg text-muted">This first milestone connects the website, backend, and database. The connection panel shows the actual backend response.</p>
            <p className="mt-4 max-w-lg text-muted">Student profiles, readiness scores, recruiter matching, and placement dashboards are planned for later phases.</p>
            <p className="mt-6 text-sm font-semibold text-navy">Reject less → Identify the gap → Help improve</p>
          </section>
          <HealthStatus />
        </div>
      </main>
      <footer className="border-t border-line px-6 py-6 text-center text-xs text-muted">JobJugaad · An explainability-first CampusLink prototype · Phase 0</footer>
    </div>
  )
}
