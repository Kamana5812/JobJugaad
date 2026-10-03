import { useState } from 'react'
import { displayTime, StatusPill } from './DashboardCard'
import { FormField, secondaryStyle, Message } from './FormField'
import { calendarErrorMessage } from '../api/calendar'

function ConstraintRow({ item, resourceName, onCancel, busy }) {
  const [reason, setReason] = useState(''), [saving, setSaving] = useState(false), [error, setError] = useState('')
  async function cancel(event) {
    event.preventDefault(); setSaving(true); setError('')
    try {
      if (reason.trim().length < 10) { setError('Enter a cancellation reason with at least 10 non-space characters.'); return }
      await onCancel(item.id, { version: item.version, reason: reason.trim() }); setReason('')
    }
    catch (failure) { setError(calendarErrorMessage(failure)) }
    finally { setSaving(false) }
  }
  return <article className="rounded-xl border border-line p-4">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-semibold text-navy">{item.label}</h3>
      <StatusPill warning={item.status === 'cancelled'}>{item.status}</StatusPill></div>
    <p className="mt-1 text-sm text-muted">{item.kind === 'exam' ? 'Exam block' : item.kind === 'available' ? 'Available' : 'Unavailable'}{resourceName && ' · ' + resourceName(item)}</p>
    <p className="mt-2 text-sm">{displayTime(item.starts_at)} – {displayTime(item.ends_at)}</p>
    {item.status === 'active' && <details className="mt-3 text-sm"><summary className="cursor-pointer font-semibold text-navy">Cancel calendar entry #{item.id}</summary>
      <form onSubmit={cancel} className="mt-3 space-y-3">
        <FormField label={'Cancellation reason for entry #' + item.id} required minLength="10" maxLength="1000" value={reason} onChange={event => setReason(event.target.value)} hint="At least 10 characters; the entry remains in history." />
        <Message error>{error}</Message><button className={secondaryStyle} disabled={busy || saving}>{saving ? 'Saving…' : 'Confirm cancellation'}</button>
      </form>
    </details>}
  </article>
}

export default function CalendarConstraintList({ data, ...props }) {
  return <div className="space-y-3">
    {data?.total === 0 && <p className="text-sm text-muted">No calendar entries recorded yet.</p>}
    {data?.items.map(item => <ConstraintRow key={item.id} item={item} {...props} />)}
  </div>
}
