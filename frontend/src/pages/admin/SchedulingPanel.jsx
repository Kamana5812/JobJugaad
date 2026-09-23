import { useState } from 'react'
import { secondaryStyle, Message } from '../../components/FormField'
import DashboardCard from '../../components/DashboardCard'
import AuditTrail from '../../components/AuditTrail'
import { errorMessage } from '../../api/student'
import ScheduleForm from './ScheduleForm'
import ProposalCard from './ProposalCard'
import InterviewList from './InterviewList'
export default function SchedulingPanel({ board, refresh }) {
  const [source, setSource] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const names = { student: id => board.students.find(item => item.id === id)?.name || 'Student #' + id,
    job: id => board.jobs.find(item => item.id === id)?.name || 'Drive #' + id }
  const pending = board.proposals.filter(item => item.status === 'pending')
  async function perform(action, success, onResult) {
    setBusy(true); setError(''); setMessage('')
    let saved = false
    try {
      await action(); saved = true; await refresh(); setMessage(success); setSource(null)
      onResult?.({ error: false, message: success }); return true
    } catch (failure) {
      const detail = saved ? 'Your change was saved, but the dashboard could not refresh. Click Refresh dashboard to see it.' : errorMessage(failure)
      setError(detail); onResult?.({ error: true, message: detail }); return saved
    }
    finally { setBusy(false) }
  }
  function resolve(item) {
    setSource(item)
    document.getElementById('schedule-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  return <div className="space-y-6">
    <DashboardCard title="01 Conflict alerts" label="Shared students · venues · panels · overlapping drives">
      <p className="mb-4 text-sm text-muted">Independent drives may run together. Overlapping drives conflict when they share a student, venue or panel. Pending proposals do not reserve a slot.</p>
      {board.conflicts.length ? <div className="space-y-3">{board.conflicts.map(conflict => {
        const item = board.interviews.find(row => row.id === conflict.other_interview_id)
        return <div key={conflict.interview_id + '-' + conflict.other_interview_id} className="rounded-xl border border-saffron-deep/30 bg-warning-soft p-4">
          <p className="text-sm">{conflict.explanation}</p>
          {item?.status === 'scheduled' && <button className={secondaryStyle + ' mt-3'} onClick={() => resolve(item)}>Propose resolution for #{item.id}</button>}
        </div>
      })}</div> : <p className="text-sm font-semibold text-growth">No overlapping bookings found in the recorded calendar.</p>}
    </DashboardCard>
    <div id="schedule-form"><ScheduleForm key={source?.id || 'new'} board={board} source={source} onClearSource={() => setSource(null)} onSaved={refresh} /></div>
    <DashboardCard title={'03 Pending approval (' + pending.length + ')'} label="The administrator makes the final decision">
      <Message error>{error}</Message><Message>{message}</Message>
      <div className="mt-4 space-y-4">{pending.length ? pending.map(proposal => <ProposalCard key={proposal.id} proposal={proposal} names={names} perform={perform} busy={busy} />)
        : <p className="text-sm text-muted">Create a proposal above to review its time, explanation and conflicts.</p>}</div>
    </DashboardCard>
    <InterviewList items={board.interviews} names={names} onResolve={resolve} perform={perform} busy={busy} />
    <DashboardCard title="05 Calendar review history" label="Latest 50 actions"><AuditTrail events={board.audit} /></DashboardCard>
  </div>
}
