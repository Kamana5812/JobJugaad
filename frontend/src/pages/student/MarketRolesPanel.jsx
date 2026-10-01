import { useMemo, useState } from 'react'
import catalogue from '../../assets/market/roles.json'
import { FormField, secondaryStyle } from '../../components/FormField'

export function filterMarketRoles(roles, query, location, experience) {
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean)
  return roles.filter(role => (!location || role.location === location) && (!experience || role.experience === experience)
    && words.every(word => [role.title, role.company, role.location, role.description, ...role.keyword_tags].join(' ').toLowerCase().includes(word)))
}
export function MarketRoleCard({ role }) {
  return <article className="rounded-xl border border-line bg-white p-5">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-medium uppercase tracking-wide text-muted">{role.company || 'Company not recorded'}</p><h3 className="mt-2 text-lg font-semibold text-navy">{role.title}</h3></div><span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-saffron-deep">Historical reference</span></div>
    <p className="mt-3 text-sm text-muted">{role.location} · {role.experience} · {role.work_type || 'Work type not recorded'}</p>
    <p className="mt-2 text-xs text-muted">Originally listed {role.listed_date} · Availability has not been checked.</p>
    <div className="mt-4 flex flex-wrap gap-2">{role.keyword_tags.map(tag => <span key={tag} className="rounded-md border border-line bg-paper px-2 py-1 text-xs text-navy">{tag}</span>)}</div>
    <p className="mt-2 text-xs leading-5 text-muted">Keyword tags found in the description by fixed text rules; they are not verified mandatory requirements.</p>
    <details className="mt-5 border-t border-line pt-4"><summary className="cursor-pointer text-sm font-semibold text-navy">Read source description & requirements</summary><p className="mt-4 whitespace-pre-line break-words text-sm leading-7 text-muted">{role.description}</p>{role.description_truncated && <p className="mt-2 text-xs text-muted">Description excerpt. View the original posting for the complete source.</p>}</details>
    <a href={role.original_url} target="_blank" rel="noopener noreferrer" className="mt-5 inline-flex text-sm font-semibold text-navy underline underline-offset-4">View original historical posting ↗</a>
    <p className="mt-2 text-xs text-muted">External LinkedIn link · it may have expired or require sign-in.</p>
  </article>
}
export default function MarketRolesPanel() {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [experience, setExperience] = useState('')
  const [page, setPage] = useState(0)
  const roles = useMemo(() => filterMarketRoles(catalogue.roles, query, location, experience), [query, location, experience])
  const locations = [...new Set(catalogue.roles.map(r => r.location))].sort()
  const levels = [...new Set(catalogue.roles.map(r => r.experience))].sort()
  function change(setter, value) { setter(value); setPage(0) }
  return <section id="market-roles" aria-labelledby="market-roles-title" className="scroll-mt-24 space-y-5">
    <div><p className="text-xs font-semibold uppercase tracking-widest text-saffron-deep">Market reference library</p><h2 id="market-roles-title" className="mt-2 text-2xl font-semibold tracking-tight text-navy">Explore market roles</h2><p className="mt-3 max-w-3xl text-sm leading-7 text-muted">Explore real job descriptions from a public 2023–2024 archive to understand role expectations. These are historical references, not current vacancies, college drives, or employer partnerships. No application is submitted through JobJugaad.</p></div>
    <div className="grid gap-4 rounded-xl border border-line bg-white p-5 sm:grid-cols-3"><FormField label="Search titles, descriptions or skills" type="search" maxLength="120" value={query} onChange={e => change(setQuery, e.target.value)} placeholder="Try Python or mechanical" /><FormField label="Recorded location" value={location} onChange={e => change(setLocation, e.target.value)}><option value="">All locations</option>{locations.map(value => <option key={value}>{value}</option>)}</FormField><FormField label="Recorded experience" value={experience} onChange={e => change(setExperience, e.target.value)}><option value="">All experience levels</option>{levels.map(value => <option key={value}>{value}</option>)}</FormField></div>
    <p role="status" className="text-sm text-muted">{roles.length} reference roles found · Curated subset of {catalogue.roles.length} records, not a representative market survey.</p>
    {!roles.length && <div className="rounded-xl border border-dashed border-line bg-white p-6"><p className="text-sm text-muted">No references match these filters.</p><button className={secondaryStyle + ' mt-4'} onClick={() => { setQuery(''); setLocation(''); setExperience(''); setPage(0) }}>Clear filters</button></div>}
    <div className="grid gap-4 lg:grid-cols-2">{roles.slice(page * 6, (page + 1) * 6).map(role => <MarketRoleCard key={role.id} role={role} />)}</div>
    {roles.length > 6 && <nav aria-label="Market reference pages" className="flex items-center justify-between gap-3"><button className={secondaryStyle} disabled={page === 0} onClick={() => setPage(p => p - 1)}>Previous</button><p className="text-xs text-muted">Page {page + 1} of {Math.ceil(roles.length / 6)}</p><button className={secondaryStyle} disabled={(page + 1) * 6 >= roles.length} onClick={() => setPage(p => p + 1)}>Next</button></nav>}
    <p className="text-xs leading-6 text-muted">Source: <a href={catalogue.source_url} target="_blank" rel="noopener noreferrer" className="underline">LinkedIn Job Postings (2023–2024)</a> by Arsh Koneru; additional scraping credited to Zoey Yuzou by the publisher. Version {catalogue.source_version}. Adapted subset: descriptions excerpted and fixed-rule keyword tags added. <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener noreferrer" className="underline">CC BY-SA 4.0</a>. Source provenance and experience labels are publisher-reported, not independently verified.</p>
  </section>
}
