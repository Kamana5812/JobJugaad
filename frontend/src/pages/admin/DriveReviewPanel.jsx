import { useEffect, useState } from 'react'
import { getCollegeJobs } from '../../api/admin'
import { errorMessage } from '../../api/student'
import { FormField, Message, secondaryStyle } from '../../components/FormField'
import { useAuth } from '../../context/AuthContext'
import MatchPanel from '../recruiter/MatchPanel'
import JobApplicationsPanel from '../recruiter/JobApplicationsPanel'
import DriveState from '../../components/DriveState'
import DemandPanel from '../../components/DemandPanel'
import ReminderControl from '../../components/ReminderControl'

export default function DriveReviewPanel() {
  const { logout } = useAuth()
  const [jobs, setJobs] = useState([])
  const [selected, setSelected] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function load() {
    setBusy(true); setError('')
    try { const rows = await getCollegeJobs(); setJobs(rows); setSelected(id => rows.some(j => String(j.id) === id) ? id : String(rows[0]?.id || '')) }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [])
  const job = jobs.find(j => String(j.id) === selected)
  return <section className="space-y-5">
    <DemandPanel admin />
    <ReminderControl />
    <h2 className="text-2xl font-bold text-navy">Drive review & human decisions</h2>
    <p className="text-sm text-muted">Review all drives in your college, override calculated recommendations with a recorded reason, and review consenting applications before scheduling.</p>
    <Message error>{error}</Message>
    <div className="flex flex-wrap items-end gap-3"><FormField label="College drive" value={selected} onChange={e => setSelected(e.target.value)}>
      <option value="">Choose a drive</option>{jobs.map(j => <option key={j.id} value={j.id}>{j.title} (#{j.id})</option>)}
    </FormField><button className={secondaryStyle} disabled={busy} onClick={load}>{busy ? 'Loading…' : 'Refresh drives'}</button></div>
    {!busy && !jobs.length && <p className="text-muted">No recruiter-created drives in this college yet.</p>}
    {job && <><DriveState key={`${job.id}-${job.version}`} job={job} admin onSaved={load} /><MatchPanel key={job.id} job={job} admin /><JobApplicationsPanel key={'applications:'+job.id} job={job} admin onExpired={() => logout(true)} /></>}
  </section>
}
