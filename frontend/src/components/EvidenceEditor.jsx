import { FormField, inputStyle, secondaryStyle } from './FormField'

export default function EvidenceEditor({ title, items, onChange, kind, limit }) {
  const skills = kind === 'skills'
  function update(index, key, value) { onChange(items.map((item, i) => i === index ? { ...item, [key]: value } : item)) }
  return <section className="rounded-2xl border border-line bg-white p-5">
    <div className="flex items-center justify-between gap-3"><h3 className="font-bold text-navy">{title}</h3><span className="text-xs text-muted">{items.length}/{limit}</span></div>
    {!items.length && <p className="mt-3 text-sm text-muted">Nothing recorded yet. Add evidence when you have it.</p>}
    <div className="mt-4 space-y-4">{items.map((item, index) => <fieldset key={index} className="rounded-xl bg-paper p-4">
      <legend className="px-1 text-xs font-bold text-muted">{title} · {index + 1}</legend>
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField label={skills ? 'Skill name' : 'Title'} value={skills ? item.skill_name : item.title} required maxLength={skills ? 80 : 160}
          onChange={(event) => update(index, skills ? 'skill_name' : 'title', event.target.value)} />
        {skills ? <FormField label="Proficiency / 100" type="number" min="0" max="100" step="0.1" required value={item.proficiency}
          onChange={(event) => update(index, 'proficiency', event.target.value)} hint="Self-reported, not a tested result." />
          : <label className="text-sm font-semibold text-navy">Description<textarea className={inputStyle + ' mt-1.5 min-h-24'} required maxLength="3000" value={item.description}
            onChange={(event) => update(index, 'description', event.target.value)} /></label>}
      </div>
      <button type="button" className="mt-3 text-xs font-semibold text-[#922B2B] underline underline-offset-4" onClick={() => onChange(items.filter((_, i) => i !== index))}>Remove {skills ? 'skill' : 'entry'} {index + 1}</button>
    </fieldset>)}</div>
    <button type="button" className={secondaryStyle + ' mt-4'} disabled={items.length >= limit}
      onClick={() => onChange([...items, skills ? { skill_name: '', proficiency: '' } : { title: '', description: '' }])}>+ Add {skills ? 'skill' : kind === 'projects' ? 'project' : 'certification'}</button>
  </section>
}
