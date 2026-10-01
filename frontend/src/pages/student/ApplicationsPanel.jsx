import { useEffect, useState } from 'react'
import { getOpportunities, errorMessage } from '../../api/student'
import { getApplications, submitApplication, withdrawApplication } from '../../api/applications'
import ApplicationCard from '../../components/ApplicationCard'
import ApplicationAction from '../../components/ApplicationAction'
import Pagination from '../../components/Pagination'
import { FormField, inputStyle, buttonStyle, secondaryStyle, Message } from '../../components/FormField'
export default function ApplicationsPanel({ studentId, dirty, onExpired }) {
  const [roles, setRoles] = useState([])
  const [data, setData] = useState(null)
  const [job, setJob] = useState('')
  const [note, setNote] = useState('')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  async function load(offset = 0) {
    setBusy(true); setError('')
    try { const [applications, opportunities] = await Promise.all([getApplications(studentId, offset), getOpportunities(studentId, { status: 'all', limit: 1 })]); setData(applications); setRoles(opportunities.roles) }
    catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [studentId])
  async function submit(event) {
    event.preventDefault(); if (!consent || dirty) return
    setBusy(true); setError(''); setNotice('')
    try { await submitApplication(studentId, { job_id: Number(job), cover_note: note.trim() }); setJob(''); setNote(''); setConsent(false); await load(); setNotice('Jugaad Ho Gaya ✓ Application submitted for human review.') }
    catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section id="applications" className="scroll-mt-6 space-y-5 rounded-xl border border-line bg-white p-6 sm:p-8">
    <div className="flex flex-wrap justify-between gap-4"><div><h2 className="text-xl font-bold text-navy">My applications</h2><p className="mt-2 text-sm leading-6 text-muted">Apply to a college drive and follow recorded recruiter decisions. Historical market references cannot receive applications.</p></div><button type="button" disabled={busy} onClick={() => load(data?.offset || 0)} className={secondaryStyle}>Refresh applications</button></div>
    <Message error>{error}</Message><Message>{notice}</Message>
    {dirty && <p className="text-sm text-critical">Save your profile changes before submitting an application.</p>}
    <form onSubmit={submit} className="space-y-4 rounded-lg bg-paper p-5"><fieldset disabled={busy || dirty} className="space-y-4">
      <FormField label="College drive" required value={job} onChange={e => setJob(e.target.value)}><option value="">Choose a drive</option>{roles.map(role => <option key={role.job_id} value={role.job_id}>{role.title} · {role.company_name} (#{role.job_id})</option>)}</FormField>
      <label htmlFor="application-note" className="block text-sm font-semibold text-navy">Cover note (optional)</label><textarea id="application-note" className={inputStyle} rows={3} maxLength={1000} value={note} onChange={e => setNote(e.target.value)} />
      <label className="flex items-start gap-3 text-sm leading-6 text-ink"><input type="checkbox" required checked={consent} onChange={e => setConsent(e.target.checked)} className="mt-1.5" /><span>I agree to share my saved profile’s matching evidence and this note with the drive’s recruiter. The submission-time evidence stays in my application history.</span></label>
      <p className="text-xs leading-5 text-muted">You may submit when weighted rules identify gaps; a recruiter makes the decision. A submission is not an interview invitation or offer.</p>
      <button disabled={busy || dirty || !job || !consent} className={buttonStyle}>{busy ? 'Please wait…' : 'Submit application →'}</button>
    </fieldset></form>
    {busy && <p role="status" className="text-sm text-muted">Loading application records…</p>}
    {data?.total === 0 && <p className="text-sm text-muted">No applications yet. Choose a college drive above to get started.</p>}
    {data?.items.map(application => <ApplicationCard key={application.id} application={application}><ApplicationAction key={application.version} application={application} onExpired={onExpired} onAction={input => withdrawApplication(studentId, application.id, input)} onSaved={() => load(data.offset)} /></ApplicationCard>)}
    <Pagination data={data} busy={busy} onPage={load} />
  </section>
}
