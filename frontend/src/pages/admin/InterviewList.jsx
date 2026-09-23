import { useState } from 'react'
import { FormField, buttonStyle, secondaryStyle, Message } from '../../components/FormField'
import DashboardCard, { displayTime, StatusPill } from '../../components/DashboardCard'
import { updateInterview } from '../../api/admin'
function InterviewRow({ item, names, onResolve, busy, perform }) {
  const [status, setStatus] = useState('cancelled')
  const [reason, setReason] = useState('')
  const [feedback, setFeedback] = useState(null)
  async function submit(event) {
    event.preventDefault()
    setFeedback(null)
    if (await perform(() => updateInterview(item.id, { status, reason }), 'Interview status saved.', setFeedback)) setReason('')
  }
  return <article className="border-t border-line py-4">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-bold text-navy">#{item.id} · {names.student(item.student_id)}</h3><StatusPill warning={item.status === 'cancelled'}>{item.status}</StatusPill></div>
    <p className="text-sm">{names.job(item.job_id)} · {item.venue} · {item.panel_id}</p>
    <p className="text-sm text-muted">{displayTime(item.scheduled_time)} – {displayTime(item.end_time)}</p>
    {item.seed_key?.startsWith('phase3-double') && <p className="mt-1 text-xs text-muted">Synthetic imported double-booking demonstration.</p>}
    {item.status === 'scheduled' && <button className={secondaryStyle + ' mt-3'} disabled={busy} onClick={() => onResolve(item)}>Propose reschedule #{item.id}</button>}
    {item.status !== 'cancelled' && <details className="mt-3 text-sm"><summary className="cursor-pointer font-semibold text-navy">Record outcome or cancellation</summary>
      <form onSubmit={submit} className="mt-3 grid gap-3 sm:grid-cols-2">
        <FormField label={'Status for interview #' + item.id} value={status} onChange={event => setStatus(event.target.value)}>
          <option value="cancelled">Cancelled</option><option value="completed">Completed</option><option value="selected">Selected</option><option value="rejected">Rejected</option>
        </FormField>
        <FormField label={'Reason for interview #' + item.id} required minLength="10" maxLength="1000" hint="Enter at least 10 characters, for example: Synthetic workflow verification." value={reason} onChange={event => setReason(event.target.value)} />
        <p className="text-xs text-muted sm:col-span-2">Selected, Completed or Rejected can be saved after {displayTime(item.end_time)}. Selected does not mean an offer or placement.</p>
        <div className="sm:col-span-2"><Message error={feedback?.error}>{feedback?.message}</Message></div>
        <button type="submit" className={buttonStyle} disabled={busy}>{busy ? 'Saving…' : 'Save interview status'}</button>
      </form>
    </details>}
  </article>
}
export default function InterviewList(props) {
  return <DashboardCard title="04 Interview calendar" label="All scheduled bookings · latest 50 other records">
    {!props.items.length && <p className="text-sm text-muted">No confirmed interviews yet.</p>}
    {props.items.map(item => <InterviewRow key={item.id} item={item} {...props} />)}
  </DashboardCard>
}
