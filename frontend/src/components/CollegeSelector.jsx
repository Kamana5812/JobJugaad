import { useState } from 'react'
import directory from '../assets/bput-colleges.json'
import { FormField } from './FormField'
export function collegeName(id) { return directory.colleges.find(c => c.id === Number(id))?.name || 'College not found' }
export default function CollegeSelector({ value, onChange, disabled, allowDemo = false, label = 'College', hint = 'Choose the same college each time you sign in. New accounts require email verification and college administrator approval.' }) {
  const [search, setSearch] = useState('')
  const query = search.trim().toLowerCase()
  const visible = directory.colleges.filter(c => (allowDemo || c.kind !== 'demo')).filter(c => c.id === Number(value) || !query || [c.name, c.code || '', c.district, ...c.courses].join(' ').toLowerCase().includes(query))
  return <div className="space-y-3"><FormField label="Find your college" type="search" value={search} maxLength="120" onChange={e => setSearch(e.target.value)} disabled={disabled} placeholder="Search name, code or district" />
    <FormField label={label} value={value} onChange={onChange} disabled={disabled} required hint={hint}>{allowDemo && <optgroup label="Demo colleges (existing accounts)">{visible.filter(c => c.kind === 'demo').map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</optgroup>}<optgroup label="BPUT directory · 2022–23 snapshot">{visible.filter(c => c.kind !== 'demo').map(c => <option key={c.id} value={c.id}>{c.name} · {c.code}</option>)}</optgroup></FormField>
    <p className="text-xs leading-5 text-muted">{directory.note} <a href={directory.source_url} target="_blank" rel="noopener noreferrer" className="underline">View official source ↗</a></p>
  </div>
}
