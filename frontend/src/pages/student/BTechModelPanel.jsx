import { useEffect, useState } from 'react'
import { getBTechModel, saveBTechModel, errorMessage } from '../../api/student'
import { FormField, Message, buttonStyle, secondaryStyle } from '../../components/FormField'
import PlacementModelCard from '../../components/PlacementModelCard'

const streams = ['Civil','Computer Science','Electrical','Electronics And Communication','Information Technology','Mechanical']
export default function BTechModelPanel({ sectionNumber = "04", studentId, onExpired }) {
  const [data,setData] = useState(null)
  const [form,setForm] = useState(null)
  const [busy,setBusy] = useState(false)
  const [dirty,setDirty] = useState(false)
  const [error,setError] = useState('')
  const [notice,setNotice] = useState('')
  async function load() {
    setBusy(true);setError('')
    try { const value=await getBTechModel(studentId);setData(value);setForm(value.inputs);setDirty(false) }
    catch (failure) { if (failure.response?.status===401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() },[studentId])
  useEffect(() => {
    if (!dirty) return
    const warn=(event) => { event.preventDefault();event.returnValue='' }
    window.addEventListener('beforeunload',warn)
    return () => window.removeEventListener('beforeunload',warn)
  },[dirty])
  function change(key,value) { setForm((current)=>({...current,[key]:value}));setDirty(true);setNotice('') }
  async function save(event) {
    event.preventDefault();setBusy(true);setError('');setNotice('')
    const inputs={...form,stream:form.stream || null}
    for (const key of ['cgpa','internships','history_of_backlogs']) inputs[key]=form[key]==='' || form[key]===null ? null : Number(form[key])
    try { const value=await saveBTechModel(studentId,inputs);setData(value);setForm(value.inputs);setDirty(false);setNotice('Jugaad Ho Gaya ✓ BTech evidence saved. Your other scores stay separate.') }
    catch (failure) { if (failure.response?.status===401) onExpired();else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section aria-labelledby="btech-model-title" className="space-y-5 rounded-3xl border border-line bg-white p-6 sm:p-8">
    <div><p className="text-xs font-bold uppercase tracking-widest text-muted">Engineering public-data Random Forest · optional signal</p>
      <h2 id="btech-model-title" className="mt-2 text-2xl font-bold text-navy"><span className="mr-3 text-saffron">{sectionNumber}</span>BTech Placement Likelihood Model</h2>
      <p className="mt-3 text-sm leading-6 text-muted">For BTech / BE students in the six engineering streams below. No MBA details needed. Trained on publisher-reported university placement records from 2013–2014; the original collection has not been independently audited.</p>
    </div>
    {data && <PlacementModelCard signal={data.signal} evaluation={data.evaluation} dirty={dirty} datasetName="Engineering Placements Prediction" splitDescription="One fixed split keeps identical modeled input profiles together, with no profile shared between training and testing." />}
    {!data && busy && <p role="status" className="text-sm text-muted">Loading BTech model inputs…</p>}
    {form && <details className="rounded-2xl bg-paper p-5"><summary className="cursor-pointer font-bold text-navy">Add or edit BTech model inputs</summary>
      <p className="mt-3 text-sm leading-6 text-muted">Use CGPA through semester 6, completed internships, and whether you have ever had a backlog—even if it is now cleared. These are saved separately from your general profile. Leave unknown values blank.</p>
      <p className="mt-2 text-xs leading-5 text-muted">The source covers CGPA 5–9 and 0–3 internships. Values outside that range are saved, but produce no prediction. Other engineering streams are not represented. Do not change your real details to fit the model.</p>
      <form onSubmit={save} className="mt-5 space-y-5"><fieldset disabled={busy} className="grid gap-5 sm:grid-cols-2">
        <FormField label="CGPA through semester 6 / 10" type="number" min="0" max="10" step="0.01" value={form.cgpa ?? ''} onChange={(event)=>change('cgpa',event.target.value)} />
        <FormField label="Engineering stream" value={form.stream ?? ''} onChange={(event)=>change('stream',event.target.value)}><option value="">Not recorded / not represented</option>{streams.map((stream)=><option key={stream} value={stream}>{stream}</option>)}</FormField>
        <FormField label="Completed internships" type="number" min="0" max="100" step="1" value={form.internships ?? ''} onChange={(event)=>change('internships',event.target.value)} />
        <FormField label="Ever had any backlog?" value={form.history_of_backlogs ?? ''} onChange={(event)=>change('history_of_backlogs',event.target.value)}><option value="">Not recorded</option><option value="0">No</option><option value="1">Yes, including cleared backlogs</option></FormField>
      </fieldset><button className={buttonStyle} disabled={busy || !dirty}>{busy ? 'Saving…' : 'Save BTech inputs & view model'}</button></form>
    </details>}
    <Message error>{error}</Message><Message>{notice}</Message>
    {!data && !busy && <button type="button" onClick={load} className={secondaryStyle}>Retry BTech panel</button>}
  </section>
}
