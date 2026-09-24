import { useEffect, useState } from 'react'
import { getPlacementModel, savePlacementModel, errorMessage } from '../../api/student'
import { FormField, Message, buttonStyle, secondaryStyle } from '../../components/FormField'
import PlacementModelCard from '../../components/PlacementModelCard'

const percentages = [['ssc_p','10th percentage'],['hsc_p','12th percentage'],['degree_p','Degree percentage'],['etest_p','Employability test percentage'],['mba_p','MBA percentage']]
const categories = [
  ['gender','Gender recorded for this model',[['F','Female'],['M','Male']]],
  ['ssc_b','10th board',[['Central','Central'],['Others','Other board']]],
  ['hsc_b','12th board',[['Central','Central'],['Others','Other board']]],
  ['hsc_s','12th stream',[['Arts','Arts'],['Commerce','Commerce'],['Science','Science']]],
  ['degree_t','Degree type',[['Comm&Mgmt','Commerce & Management'],['Sci&Tech','Science & Technology'],['Others','Other degree']]],
  ['workex','Prior work experience',[['No','No'],['Yes','Yes']]],
  ['specialisation','MBA specialisation',[['Mkt&Fin','Marketing & Finance'],['Mkt&HR','Marketing & HR']]],
]
export default function PlacementModelPanel({ studentId, onExpired }) {
  const [data, setData] = useState(null)
  const [form, setForm] = useState(null)
  const [busy, setBusy] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  async function load() {
    setBusy(true); setError('')
    try { const value = await getPlacementModel(studentId); setData(value); setForm(value.inputs); setDirty(false) }
    catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [studentId])
  useEffect(() => {
    if (!dirty) return
    const warn = (event) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])
  function change(key, value) { setForm((current) => ({ ...current, [key]: value })); setDirty(true); setNotice('') }
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('')
    const inputs = { ...form }
    for (const [key] of percentages) inputs[key] = form[key] === '' || form[key] === null ? null : Number(form[key])
    for (const [key] of categories) inputs[key] = form[key] || null
    try {
      const saved = await savePlacementModel(studentId, inputs)
      setData(saved); setForm(saved.inputs); setDirty(false)
      setNotice('Jugaad Ho Gaya ✓ Academic inputs saved. Weighted readiness stays separate.')
    } catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section aria-labelledby="placement-model-title" className="space-y-5 rounded-3xl border border-line bg-white p-6 sm:p-8">
    <div><p className="text-xs font-bold uppercase tracking-widest text-muted">Public-data Random Forest · optional signal</p>
      <h2 id="placement-model-title" className="mt-2 text-2xl font-bold text-navy"><span className="mr-3 text-saffron">04</span>Placement Likelihood Model</h2>
      <p className="mt-3 text-sm leading-6 text-muted">Trained using the real public Campus Recruitment dataset (215 records: 172 training, 43 testing). This MBA-oriented model uses academic records and prior work experience. It does not use your skills, projects, resume or weighted readiness.</p>
    </div>
    {data && <PlacementModelCard signal={data.signal} evaluation={data.evaluation} dirty={dirty} />}
    {!data && busy && <p role="status" className="text-sm text-muted">Loading your academic model inputs…</p>}
    {form && <details className="rounded-2xl bg-paper p-5">
      <summary className="cursor-pointer font-bold text-navy">Add or edit academic model inputs</summary>
      <p className="mt-3 text-sm leading-6 text-muted">Use only recorded percentages, including MBA results. Leave unavailable or inapplicable values blank; no prediction is made until all 12 fields are present. Do not convert CGPA without your institution’s official rule or substitute an unrelated assessment for an employability test.</p>
      <p className="mt-2 text-xs leading-5 text-muted">The dataset only provides Female/Male categories and two MBA specialisations. Leave the field blank if neither applies or you prefer not to provide it. These fields are optional; they do not affect your access to other features.</p>
      <form onSubmit={save} className="mt-5 space-y-5">
        <fieldset disabled={busy} className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {percentages.map(([key,label]) => <FormField key={key} label={`${label} / 100`} type="number" min="0" max="100" step="0.01" value={form[key] ?? ''} onChange={(event) => change(key,event.target.value)} />)}
          {categories.map(([key,label,options]) => <FormField key={key} label={label} value={form[key] ?? ''} onChange={(event) => change(key,event.target.value)}><option value="">Not recorded / not applicable</option>{options.map(([value,text]) => <option key={value} value={value}>{text}</option>)}</FormField>)}
        </fieldset>
        <button className={buttonStyle} disabled={busy || !dirty}>{busy ? 'Saving…' : 'Save academic inputs & view model'}</button>
      </form>
    </details>}
    <Message error>{error}</Message><Message>{notice}</Message>
    {!data && !busy && <button type="button" onClick={load} className={secondaryStyle}>Retry model panel</button>}
  </section>
}
