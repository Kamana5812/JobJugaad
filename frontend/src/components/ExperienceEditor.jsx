import { FormField, secondaryStyle } from './FormField'

export default function ExperienceEditor({ items, onChange }) {
  function change(index, key, value) { onChange(items.map((item, i) => i === index ? { ...item, [key]: value } : item)) }
  return <section className="space-y-4"><h3 className="font-bold text-navy">Internships and experience</h3>
    <p className="text-xs text-muted">Self-reported experience for human review. These records do not change the weighted readiness formula.</p>
    {items.map((item, index) => <div key={index} className="grid gap-4 rounded-xl border border-line p-4 sm:grid-cols-2">
      <label className="text-sm text-navy">Type<select className="mt-2 block w-full rounded-lg border border-line p-3" value={item.kind} onChange={e => change(index, 'kind', e.target.value)}><option value="internship">Internship</option><option value="employment">Employment</option><option value="volunteering">Volunteering</option></select></label>
      <FormField label="Organisation" required maxLength={160} value={item.organization} onChange={e => change(index, 'organization', e.target.value)} />
      <FormField label="Role" required maxLength={160} value={item.role} onChange={e => change(index, 'role', e.target.value)} />
      <FormField label="Reference (optional)" maxLength={300} value={item.reference ?? ''} onChange={e => change(index, 'reference', e.target.value || null)} />
      <label className="text-sm text-navy sm:col-span-2">Work and evidence<textarea required maxLength={3000} className="mt-2 block w-full rounded-lg border border-line p-3" value={item.description} onChange={e => change(index, 'description', e.target.value)} /></label>
      <button type="button" className={secondaryStyle} onClick={() => onChange(items.filter((_, i) => i !== index))}>Remove experience {index + 1}</button>
    </div>)}
    <button type="button" className={secondaryStyle} disabled={items.length >= 20} onClick={() => onChange([...items, { kind: 'internship', organization: '', role: '', description: '', reference: null }])}>Add experience</button>
  </section>
}
