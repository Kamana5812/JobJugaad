import { Link } from 'react-router-dom'
import logo from '../assets/brand/logo-light.svg'
export default function SiteFooter() {
  return <footer className="border-t border-line bg-white px-5 py-8 sm:px-8"><div className="mx-auto flex max-w-7xl flex-col justify-between gap-6 sm:flex-row sm:items-center"><div><Link to="/" aria-label="JobJugaad home"><img src={logo} width="2048" height="682" alt="JobJugaad" loading="lazy" className="h-auto w-36" /></Link><p className="mt-2 text-xs text-muted">Explainability-first campus placement.</p></div><div className="text-xs leading-6 text-muted"><p>College workspaces · Demonstration records remain in separate demo colleges.</p><p>Hiring notifications appear in-app. People make the final decisions.</p></div><Link to="/auth" className="text-sm font-medium text-navy hover:underline">Open your workspace →</Link></div></footer>
}
