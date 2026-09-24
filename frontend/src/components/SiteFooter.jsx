import { Link } from 'react-router-dom'
import logo from '../assets/brand/logo-dark.svg'
export default function SiteFooter() {
  return <footer className="bg-navy-dark px-5 py-10 text-white sm:px-8">
    <div className="mx-auto flex max-w-7xl flex-col justify-between gap-8 sm:flex-row sm:items-center">
      <div><Link to="/" aria-label="JobJugaad home"><img src={logo} width="2048" height="682" alt="JobJugaad" loading="lazy" className="h-auto w-56" /></Link><p className="mt-3 text-sm text-white/80">Placement ka Jugaad, AI ke Saath.</p></div>
      <div className="text-sm leading-7 text-white/80"><p className="font-semibold text-white">Built for BPUT Hackathon 2026 · CampusLink</p><p>Explainability-first. Human decisions, clear reasons.</p><p className="mt-2 text-xs">Public prototype · synthetic placement workflow records.</p></div>
    </div>
  </footer>
}
