import { useState } from 'react'
import { createJob } from '../../api/recruiter'
import { errorMessage } from '../../api/student'
import { FormField, buttonStyle, secondaryStyle, Message } from '../../components/FormField'

const initial = { title: '', ctc: '', min_cgpa: '6', max_backlogs: '0', branches: 'CSE, ECE', min_match_score: '60', assessment_benchmark: '60' }
const initialWeights = { skills: 40, projects: 20, academics: 20, assessments: 15, certifications: 5 }
export default function DriveForm({ onCreated }) {
  const [form, setForm] = useState(initial)
  const [skills, setSkills] = useState([{ skill_name: '', min_proficiency: '60' }])
  const [weights, setWeights] = useState(initialWeights)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const change = key => event => setForm({ ...form, [key]: event.target.value })
  function changeSkill(index, key, value) { setSkills(skills.map((s, i) => i === index ? { ...s, [key]: value } : s)) }
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const payload = { title: form.title, ctc: Number(form.ctc), min_cgpa: Number(form.min_cgpa), max_backlogs: Number(form.max_backlogs),
        eligible_branches: form.branches.split(',').map(s => s.trim()),
        required_skills: skills.map(s => ({ ...s, min_proficiency: Number(s.min_proficiency) })),
        weights, min_match_score: Number(form.min_match_score), assessment_benchmark: Number(form.assessment_benchmark) }
      const job = await createJob(payload)
      setForm(initial); setSkills([{ skill_name: '', min_proficiency: '60' }]); setWeights(initialWeights); onCreated(job)
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section className="rounded-3xl border border-line bg-white p-6 shadow-sm sm:p-8">
    <h2 className="text-xl font-bold text-navy"><span className="mr-2 text-saffron-deep">03</span>Create a drive</h2>
    <p className="mt-2 text-sm text-muted">Define the role and its requirements. All details below are editable before creation.</p>
    <form onSubmit={submit} className="mt-5 space-y-5">
      <FormField label="Role / drive title" required maxLength="160" value={form.title} onChange={change('title')} />
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField label="CTC (₹ lakh / year)" type="number" min="0.01" max="1000" step="0.01" required value={form.ctc} onChange={change('ctc')} />
        <FormField label="Minimum CGPA /10" type="number" min="0" max="10" step="0.1" required value={form.min_cgpa} onChange={change('min_cgpa')} />
        <FormField label="Maximum backlogs" type="number" min="0" max="100" step="1" required value={form.max_backlogs} onChange={change('max_backlogs')} />
      </div>
      <FormField label="Eligible branches" hint="Comma-separated exact branch names, for example CSE, ECE." required value={form.branches} onChange={change('branches')} />
      <fieldset className="space-y-3"><legend className="mb-2 text-sm font-bold text-navy">Required skills and target proficiency</legend>
        {skills.map((skill, index) => <div key={index} className="grid grid-cols-[minmax(0,1fr)_5rem_auto] sm:grid-cols-[minmax(0,1fr)_7rem_auto] items-end gap-2">
          <FormField label={'Skill ' + (index + 1)} required maxLength="80" value={skill.skill_name} onChange={e => changeSkill(index, 'skill_name', e.target.value)} />
          <FormField label="Target /100" aria-label={'Target for skill ' + (index + 1)} type="number" min="1" max="100" required value={skill.min_proficiency} onChange={e => changeSkill(index, 'min_proficiency', e.target.value)} />
          <button type="button" aria-label={'Remove skill ' + (index + 1)} className={secondaryStyle} disabled={skills.length === 1} onClick={() => setSkills(skills.filter((_, i) => i !== index))}>×</button>
        </div>)}
        <button type="button" className={secondaryStyle} disabled={skills.length >= 20} onClick={() => setSkills([...skills, { skill_name: '', min_proficiency: '60' }])}>Add skill</button>
        <p className="text-xs text-muted">Skill targets contribute to the weighted score; CGPA, branch and backlog limits are hard eligibility rules.</p>
      </fieldset>
      <details className="rounded-xl border border-line p-4">
        <summary className="cursor-pointer text-sm font-bold text-navy">Scoring settings · proposed, unvalidated assumptions</summary>
        <p className="my-3 text-xs text-muted">Every component is normalized to 0–100. Weights must total 100%. No calibration or trained model is used.</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{Object.entries(weights).map(([key, value]) =>
          <FormField key={key} label={key + ' weight %'} type="number" min="0" max="100" step="1" required value={value} onChange={e => setWeights({ ...weights, [key]: Number(e.target.value) })} />)}</div>
        <p className="my-3 text-sm font-bold">Total: {Object.values(weights).reduce((a, b) => a + b, 0)}%</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <FormField label="Shortlist threshold /100" type="number" min="0" max="100" step="0.01" required value={form.min_match_score} onChange={change('min_match_score')} />
          <FormField label="Assessment review benchmark /100" type="number" min="0" max="100" step="0.1" required value={form.assessment_benchmark} onChange={change('assessment_benchmark')} hint="A review flag; not a separate hard eligibility rule." />
        </div>
      </details>
      <Message error>{error}</Message>
      <button disabled={busy} className={buttonStyle}>{busy ? 'Creating…' : 'Create drive'}</button>
    </form>
  </section>
}
