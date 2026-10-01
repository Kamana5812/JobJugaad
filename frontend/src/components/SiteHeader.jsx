import { Link, NavLink } from 'react-router-dom'
import logo from '../assets/brand/logo-light.svg'
import { roleHome } from '../context/roleHome'
import { buttonStyle, secondaryStyle } from './FormField'
import { PortalIcon, portals } from './PortalIdentity'

export default function SiteHeader({ user, logout }) {
  const portal = portals.find(item => item.role === user?.role)
  return <header className="sticky top-0 z-30 border-b border-line bg-white/95 backdrop-blur">
    <nav aria-label="Main navigation" className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-3 sm:px-8">
      <Link to="/" aria-label="JobJugaad home" className="shrink-0 rounded-lg focus-visible:outline-2 focus-visible:outline-navy"><img src={logo} alt="JobJugaad" width="2048" height="682" className="h-auto w-36 sm:w-40" /></Link>
      {user ? <div className="flex flex-wrap items-center gap-4 text-sm font-semibold text-navy">
        <NavLink to={roleHome(user.role)} className="flex items-center gap-2"><PortalIcon role={user.role} className="h-5 w-5" />{portal?.name}</NavLink>
        {user.role === 'student' && <NavLink to="/student/offers">My offers</NavLink>}
        <NavLink to="/notifications">Notifications</NavLink><button onClick={logout} className={secondaryStyle}>Log out</button>
      </div> : <div className="flex flex-wrap items-center gap-4 text-sm font-semibold text-navy sm:gap-6">
        <a href="/#portals" className="hidden hover:underline sm:inline">Workspaces</a><a href="/#explainability" className="hidden hover:underline lg:inline">How it works</a>
        <Link to="/auth" className="rounded px-1 py-2 hover:underline focus-visible:outline-2 focus-visible:outline-navy">Sign in</Link><Link to="/auth" className={buttonStyle}>Get started <span aria-hidden="true" className="ml-2">↗</span></Link>
      </div>}
    </nav>
  </header>
}
