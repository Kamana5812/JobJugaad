import { useState } from 'react'
import { FormField, buttonStyle, secondaryStyle } from '../../components/FormField'
import { displayTime, StatusPill } from '../../components/DashboardCard'
import { reviewSchedule, recheckSchedule } from '../../api/admin'
export default function ProposalCard({ proposal, names, perform, busy }) {
  const [reason, setReason] = useState('')
  async function submit(event) {
    event.preventDefault()
    const action = event.nativeEvent.submitter?.value
    if (!['approve', 'reject'].includes(action)) return
    const success = await perform(() => reviewSchedule(proposal.id, { action, reason, version: proposal.version }),
      action === 'approve' ? 'Jugaad Ho Gaya ✓ — the approved slot is now confirmed.' : 'Proposal rejected; the confirmed calendar is unchanged.')
    if (success) setReason('')
  }
  return <article className="rounded-xl border border-line p-4">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-bold text-navy">Proposal #{proposal.id} · {names.student(proposal.student_id)}</h3>
      <StatusPill warning>Pending approval</StatusPill></div>
    <p className="text-sm text-muted">{names.job(proposal.job_id)} · {proposal.venue} · {proposal.panel_id}</p>
    <p className="mt-3 text-sm">Requested: {displayTime(proposal.requested_time)}</p>
    <p className="font-semibold text-navy">Proposed: {displayTime(proposal.scheduled_time)} – {displayTime(proposal.end_time)}</p>
    <p className="mt-3 text-sm">{proposal.explanation}</p>
    {!!proposal.conflicts.length && <ul className="mt-2 space-y-2 text-sm">{proposal.conflicts.map(conflict => <li key={conflict.interview_id}>{conflict.explanation}</li>)}</ul>}
    {proposal.reschedule_interview_id && <p className="mt-2 text-sm text-muted">Approval replaces interview #{proposal.reschedule_interview_id}; its original record remains in history.</p>}
    <form onSubmit={submit} className="mt-4 space-y-3">
      <FormField label={'Review reason for proposal #' + proposal.id} required minLength="10" maxLength="1000" value={reason} onChange={event => setReason(event.target.value)} />
      <div className="flex flex-wrap gap-2">
        <button className={buttonStyle} value="approve" disabled={busy}>Approve proposal #{proposal.id}</button>
        <button className={secondaryStyle} value="reject" disabled={busy}>Reject proposal #{proposal.id}</button>
        <button type="button" className={secondaryStyle} disabled={busy} onClick={() => perform(() => recheckSchedule(proposal.id, proposal.version), 'Availability rechecked. Review the updated time before approving.')}>Recheck availability</button>
      </div>
    </form>
  </article>
}
