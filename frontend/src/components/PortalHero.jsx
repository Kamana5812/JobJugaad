import studentHero from '../assets/hero/student.png'
import recruiterHero from '../assets/hero/recruiter.png'
import adminHero from '../assets/hero/admin.png'
import { portals, PortalIcon } from './PortalIdentity'

const images = { student: studentHero, recruiter: recruiterHero, admin: adminHero }
export default function PortalHero({ role, collegeId, description, children }) {
  const portal = portals.find(item => item.role === role)
  const dark = role === 'admin'
  return <header className={`overflow-hidden rounded-3xl border border-line ${dark ? 'bg-navy-dark text-white' : role === 'student' ? 'bg-warning-soft text-navy' : 'bg-growth-soft text-navy'}`}>
    <div className="grid items-center gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_1.15fr]">
      <div><p className={`flex items-center gap-2 text-xs font-bold uppercase tracking-widest ${dark ? 'text-saffron' : 'text-navy'}`}><PortalIcon role={role} className="h-5 w-5" />{portal.label} portal · Demo College {collegeId}</p>
        <h1 className="mt-4 text-3xl font-bold leading-tight tracking-tight sm:text-4xl">{portal.name}</h1><p className={`mt-4 max-w-xl text-sm leading-7 ${dark ? 'text-white/80' : 'text-navy/80'}`}>{description || portal.line}</p>
        {children && <div className="mt-5 flex flex-wrap gap-3">{children}</div>}
      </div>
      <img src={images[role]} alt="" width="2172" height="724" className="h-auto w-full rounded-2xl bg-paper" />
    </div>
    <p className={`border-t px-6 py-3 text-xs leading-5 sm:px-8 ${dark ? 'border-white/15 text-white/70' : 'border-navy/10 text-navy/70'}`}>Explainability-first · Public prototype with synthetic workflow records · People make the final decisions.</p>
  </header>
}
export function PortalSections({ label, items }) {
  return <nav aria-label={label} className="flex flex-wrap gap-2 rounded-2xl border border-line bg-white p-2">{items.map(([id, title]) => <a key={id} href={'#' + id} className="rounded-xl px-4 py-2.5 text-sm font-semibold text-navy transition hover:bg-paper focus-visible:outline-2 focus-visible:outline-navy">{title} <span aria-hidden="true" className="ml-1 text-muted">↓</span></a>)}</nav>
}
