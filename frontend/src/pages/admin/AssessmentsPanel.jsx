import { useEffect, useState } from 'react'
import { getAssessments, recordAssessment, withdrawAssessment } from '../../api/assessments'
import { errorMessage } from '../../api/student'
import AssessmentRecords from '../../components/AssessmentRecords'
import { FormField, Message, buttonStyle, secondaryStyle } from '../../components/FormField'

const empty = {student_id:'', kind:'aptitude', skill_name:'', title:'', source:'', reference:'', assessed_on:'', score:'', maximum:'100', reason:'', use_for_scoring:false}
export default function AssessmentsPanel() {
  const [form, setForm] = useState(empty)
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [offset, setOffset] = useState(0)
  const [filter, setFilter] = useState('')
  const [applied, setApplied] = useState('')
  const change = (key, value) => setForm(current => ({...current, [key]:value}))
  async function load() {
    setError(''); setBusy(true)
    try { setData(await getAssessments(null, {student_id:applied || undefined, offset, limit:20})) }
    catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  useEffect(() => { load() }, [offset, applied])
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      const row = await recordAssessment({...form, student_id:Number(form.student_id), score:Number(form.score), maximum:Number(form.maximum),
        assessed_on:new Date(form.assessed_on).toISOString(), skill_name:form.kind === 'skill' ? form.skill_name : null})
      setForm(empty); setNotice(`Assessment #${row.id} recorded with provenance. Profile scores were not overwritten.`)
      await load()
    } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  async function withdraw(id, reason) {
    setBusy(true); setError(''); setNotice('')
    try { await withdrawAssessment(id, reason); setNotice(`Record #${id} withdrawn. Original evidence remains visible.`); await load() }
    catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  return <section className="space-y-6 rounded-xl border border-line bg-white p-6 sm:p-8">
    <header><h2 className="text-xl font-bold text-navy">Assessment evidence</h2>
      <p className="mt-2 text-sm leading-6 text-muted">Record reviewed external results with source and reference. Staff entry is a human declaration, not independent exam authentication. Evidence-only is the default. Explicit adoption replaces the corresponding scoring input; latest assessment date wins, ties by record ID. Withdraw an incorrect result to restore earlier evidence or the self-report. Rerun matching and support after a change.</p></header>
    <form onSubmit={save} className="space-y-4">
      <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <FormField label="Student ID" type="number" min={1} step={1} required value={form.student_id} onChange={e=>change('student_id',e.target.value)} />
        <FormField label="Assessment type" value={form.kind} onChange={e=>change('kind',e.target.value)}>
          {['aptitude','communication','interview','skill'].map(kind=><option key={kind} value={kind}>{kind}</option>)}</FormField>
        {form.kind === 'skill' && <FormField label="Assessed skill" required maxLength={80} value={form.skill_name} onChange={e=>change('skill_name',e.target.value)} />}
        {[['title','Assessment title',160],['source','Source / provider',160],['reference','Result reference',200]].map(([key,label,length])=>
          <FormField key={key} label={label} required maxLength={length} value={form[key]} onChange={e=>change(key,e.target.value)} />)}
        <FormField label="Assessment date and time" type="datetime-local" required hint="Uses your browser timezone; use the time shown on the source result." value={form.assessed_on} onChange={e=>change('assessed_on',e.target.value)} />
        <FormField label="Original score" type="number" min={0} max={100000} step="any" required value={form.score} onChange={e=>change('score',e.target.value)} />
        <FormField label="Maximum score" type="number" min={0.000001} max={100000} step="any" required value={form.maximum} onChange={e=>change('maximum',e.target.value)} />
        <FormField label="Review context / reason" required minLength={10} maxLength={1000} value={form.reason} onChange={e=>change('reason',e.target.value)} />
        <label className="flex items-start gap-3 text-sm text-navy"><input type="checkbox" checked={form.use_for_scoring} onChange={e=>change('use_for_scoring',e.target.checked)} />Adopt this reviewed result for readiness, matching and support scoring. The original self-report is retained.</label>
      </fieldset>
      <button className={buttonStyle} disabled={busy}>{busy ? 'Saving / loading…' : 'Record reviewed result'}</button>
    </form>
    <Message error>{error}</Message><Message>{notice}</Message>
    <form onSubmit={event=>{event.preventDefault();setOffset(0);setApplied(filter)}} className="flex flex-wrap items-end gap-3">
      <FormField label="Filter by student ID (optional)" type="number" min={1} step={1} value={filter} onChange={e=>setFilter(e.target.value)} />
      <button className={secondaryStyle} disabled={busy}>Apply filter</button><button type="button" className={secondaryStyle} disabled={busy} onClick={load}>Refresh records</button>
    </form>
    {data && <><AssessmentRecords items={data.items} onWithdraw={withdraw} busy={busy} />
      {!data.items.length && <p className="text-sm text-muted">No assessment evidence found. Existing self-reports are not relabeled as verified.</p>}
      <div className="flex items-center gap-3"><button className={secondaryStyle} disabled={busy || !offset} onClick={()=>setOffset(Math.max(0,offset-20))}>Previous</button>
        <span className="text-sm text-muted">{data.total} records · page {offset/20+1}</span><button className={secondaryStyle} disabled={busy || offset+20>=data.total} onClick={()=>setOffset(offset+20)}>Next</button></div></>}
  </section>
}
