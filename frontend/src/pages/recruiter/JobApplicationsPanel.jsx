import { useEffect, useState } from 'react'
import { getJobApplications, reviewApplication } from '../../api/applications'
import { errorMessage } from '../../api/student'
import ApplicationCard from '../../components/ApplicationCard'
import ApplicationAction from '../../components/ApplicationAction'
import ApplicationProfile from '../../components/ApplicationProfile'
import Pagination from '../../components/Pagination'
import { secondaryStyle, Message } from '../../components/FormField'
import { getCollegeApplications, reviewCollegeApplication } from '../../api/admin'
export default function JobApplicationsPanel({ job, onExpired, admin = false }) {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function load(offset = 0) {
    setBusy(true); setError('')
    try { setData(await (admin ? getCollegeApplications : getJobApplications)(job.id, offset)) }
    catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [job.id, admin])
  return <section id="applications" className="scroll-mt-6 space-y-5 rounded-xl border border-line bg-white p-6 sm:p-8">
    <div className="flex flex-wrap justify-between gap-4"><div><h2 className="text-xl font-bold text-navy">Student applications · {job.title}</h2><p className="mt-2 text-sm leading-6 text-muted">Student submissions are separate from the college-wide matching shortlist. Review the frozen evidence and record a reason visible to the student.</p></div><button className={secondaryStyle} disabled={busy} onClick={() => load(data?.offset || 0)}>Refresh applications</button></div>
    <Message error>{error}</Message>{busy && <p role="status">Loading student submissions…</p>}
    {data?.total === 0 && <p className="rounded-lg bg-paper p-4 text-sm text-muted">No student has applied to this drive yet.</p>}
    <p className="text-sm text-navy">After recording Shortlisted, the administrator can choose this student and drive in Scheduling. Closed applications cannot be reopened from matching.</p>
    {data?.items.map(application => <ApplicationCard key={application.id} application={application}><ApplicationAction key={application.version} recruiter application={application} onExpired={onExpired} onAction={input => (admin ? reviewCollegeApplication : reviewApplication)(job.id, application.id, input)} onSaved={() => load(data.offset)} /><ApplicationProfile key={`profile-${application.version}`} jobId={job.id} application={application} admin={admin} onExpired={onExpired} /></ApplicationCard>)}
    <Pagination data={data} busy={busy} onPage={load} />
  </section>
}
