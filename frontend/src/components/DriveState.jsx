import { useState } from 'react'
import { changeDriveState } from '../api/driveWorkflow'
import { errorMessage } from '../api/student'
import { FormField, Message, secondaryStyle } from './FormField'

export default function DriveState({ job, admin = false, onSaved }) {
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function save(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const result = await changeDriveState(admin, job.id,
        { is_open: !job.is_open, version: job.version, reason })
      setReason(''); await onSaved(result)
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section className="space-y-4 rounded-xl border border-line bg-white p-6">
    <h3 className="font-bold text-navy">{job.title} · {job.is_open ? 'Open' : 'Closed'}</h3>
    {job.description && <details><summary className="cursor-pointer text-sm font-semibold">Recorded job description</summary><p className="mt-3 whitespace-pre-wrap text-sm">{job.description}</p></details>}
    <p className="text-sm text-muted">Closing stops new applications, matching runs and new interview proposals. Existing evidence, applications, interviews and offers remain available. Reopening is a separate audited action.</p>
    <form onSubmit={save} className="space-y-3"><FormField label="Drive state change reason" required minLength={10} maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} />
      <Message error>{error}</Message><button className={secondaryStyle} disabled={busy}>{busy ? 'Saving…' : job.is_open ? 'Close drive to new activity' : 'Reopen drive'}</button></form>
    <details><summary className="cursor-pointer text-sm font-semibold">State history ({job.lifecycle_events?.length || 0})</summary>
      {job.lifecycle_events?.map((event, index) => <p key={index} className="mt-3 text-sm">{event.is_open ? 'Reopened' : 'Closed'} · {event.actor_role} #{event.actor_user_id} · {new Date(event.created_at).toLocaleString()}<br />{event.reason}</p>)}
    </details>
  </section>
}
