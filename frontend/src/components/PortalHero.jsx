import { collegeName } from './CollegeSelector'
import { portals, PortalIcon } from './PortalIdentity'

export default function PortalHero({ role, collegeId, description, children }) {
  const portal = portals.find(item => item.role === role)
  return <header className="border-b border-line pb-6">
    <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
      <div><p className="flex items-center gap-2 text-xs font-medium text-muted"><PortalIcon role={role} className="h-4 w-4" />{portal.label} workspace<span aria-hidden="true">/</span>{collegeName(collegeId)}</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-navy sm:text-4xl">{portal.name}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{description || portal.line}</p>
      </div>{children && <div className="flex shrink-0 flex-wrap gap-3">{children}</div>}
    </div>
    <p className="mt-5 flex items-center gap-2 text-xs text-muted"><span className="rounded border border-line bg-white px-2 py-0.5 font-medium text-navy">Demo environment</span>Demonstration service · Existing demo workflows are synthetic. People make the final decisions.</p>
  </header>
}
export function PortalSections({ label, items }) {
  return <nav aria-label={label} className="flex flex-wrap gap-1 border-b border-line pb-2">{items.map(([id, title]) => <a key={id} href={'#' + id} className="rounded-lg px-4 py-2.5 text-sm font-medium text-muted transition hover:bg-white hover:text-navy focus-visible:outline-2 focus-visible:outline-navy">{title}</a>)}</nav>
}
