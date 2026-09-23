import { useEffect, useState } from 'react'
import { FormField, buttonStyle, Message, secondaryStyle } from '../../components/FormField'
import DashboardCard from '../../components/DashboardCard'
import { getSupport, runSupport } from '../../api/admin'
import { errorMessage } from '../../api/student'
import SupportCard from './SupportCard'
export default function SupportPanel({ jobs }) {
  const [jobId, setJobId] = useState(jobs.find(job => job.name === 'Simulated Cloud Support Track')?.id || jobs[0]?.id || '')
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [page, setPage] = useState(0)
  useEffect(() => {
    let active = true
    setReport(null); setError(''); setPage(0)
    if (!jobId) return
    setBusy(true)
    getSupport(jobId).then(value => { if (active) setReport(value) })
      .catch(failure => { if (active) setError(errorMessage(failure)) })
      .finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [jobId])
  async function run() {
    setBusy(true); setError('')
    try { setReport(await runSupport(Number(jobId))); setPage(0) }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  const pageSize = 5
  return <div className="space-y-6">
    <DashboardCard title="Placement support review" label="Simple rules · suggestions for a human">
      <p className="mb-4 text-sm text-muted">Review measurable indicators and the student’s circumstances together. These flags suggest support; they do not predict failure. Missing interview scores are recorded as unknown.</p>
      <div className="grid items-end gap-4 sm:grid-cols-[1fr_auto]">
        <FormField label="Target role for support checks" value={jobId} onChange={event => setJobId(event.target.value)} disabled={busy}>
          <option value="">Choose a role</option>{jobs.map(job => <option key={job.id} value={job.id}>{job.name} (#{job.id})</option>)}</FormField>
        <button className={buttonStyle} disabled={busy || !jobId} onClick={run}>{busy ? 'Checking records…' : 'Run support checks'}</button>
      </div>
      <div className="mt-4"><Message error>{error}</Message></div>
      {report && <div className="mt-4 rounded-xl bg-paper p-4 text-sm">
        <p className="font-semibold text-navy">{report.total_evaluated} profiles checked · {report.flagged_count} meet all three indicators · {report.active_count} awaiting review</p>
        <p className="mt-2">{report.unknown_interview_score_count} profiles have an unknown interview score.</p>
        <p className="mt-2 text-muted">{report.methodology}</p>
        <p className="mt-2 text-muted">Rerunning unchanged evidence preserves reviews. Changed evidence reopens the flag for a fresh review.</p>
      </div>}
    </DashboardCard>
    {report && !report.students.length && <p className="rounded-xl border border-line bg-white p-5 text-sm">{report.total_evaluated ? 'No profile meets all three support thresholds for this role.' : 'No saved checks yet. Run support checks for this role.'}</p>}
    {report?.students.slice(page * pageSize, (page + 1) * pageSize).map(student => <SupportCard key={student.id} student={student} onReviewed={setReport} />)}
    {report?.students.length > pageSize && <nav aria-label="Support results pages" className="flex items-center justify-between gap-3">
      <button className={secondaryStyle} disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
      <p className="text-sm">Page {page + 1} of {Math.ceil(report.students.length / pageSize)}</p>
      <button className={secondaryStyle} disabled={(page + 1) * pageSize >= report.students.length} onClick={() => setPage(page + 1)}>Next</button>
    </nav>}
  </div>
}
