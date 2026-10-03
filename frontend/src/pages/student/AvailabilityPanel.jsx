import { useCallback, useEffect, useState } from 'react'
import { getStudentAvailability, createStudentAvailability, cancelStudentAvailability, calendarErrorMessage } from '../../api/calendar'
import DashboardCard from '../../components/DashboardCard'
import CalendarWindowFields, { initialWindow, windowInput } from '../../components/CalendarWindowFields'
import CalendarConstraintList from '../../components/CalendarConstraintList'
import Pagination from '../../components/Pagination'
import { Message, buttonStyle, secondaryStyle } from '../../components/FormField'

export default function AvailabilityPanel({ studentId }) {
  const [data, setData] = useState(null), [offset, setOffset] = useState(0), [form, setForm] = useState(initialWindow)
  const [busy, setBusy] = useState(false), [saving, setSaving] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('')
  const refresh = useCallback(async () => {
    setBusy(true); setError('')
    try { setData(await getStudentAvailability(studentId, offset)) } catch (failure) { setError(calendarErrorMessage(failure)) }
    finally { setBusy(false) }
  }, [studentId, offset])
  useEffect(() => { refresh() }, [refresh])
  const change = key => event => { setForm({ ...form, [key]: event.target.value }); setMessage('') }
  async function save(event) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('')
    let saved = false
    try {
      await createStudentAvailability(studentId, windowInput(form)); saved = true; setForm(current => ({ ...current, label: '' }))
      await refresh(); setMessage('Your calendar entry is saved. Confirmed interviews remain scheduled; contact your placement officer if a booking needs to change.')
    } catch (failure) { setError(saved ? 'Entry saved, but the list could not refresh. Click Refresh availability.' : failure.isAxiosError ? calendarErrorMessage(failure) : failure.message) }
    finally { setSaving(false) }
  }
  async function cancel(id, input) {
    await cancelStudentAvailability(studentId, id, input); await refresh()
    setMessage('Entry cancelled and kept in history. Confirmed interviews remain scheduled.')
  }
  return <DashboardCard title="My interview availability" label="Your dated calendar windows">
    <p className="text-sm text-muted">Times use your browser timezone ({Intl.DateTimeFormat().resolvedOptions().timeZone}). Unavailable windows block new proposals. With active Available entries, the entire interview must fit recorded windows. If no window fits the next seven days, no slot is proposed; cancel or replace outdated entries. Your college may also require availability.</p>
    <p className="mt-2 text-sm text-muted">Pending proposals are rechecked before approval. Calendar edits do not automatically reschedule or cancel a confirmed booking.</p>
    <details className="my-4 rounded-xl border border-line p-4"><summary className="cursor-pointer text-sm font-semibold text-navy">Add my availability</summary>
      <form onSubmit={save} className="mt-4 space-y-4"><fieldset disabled={saving || busy} className="grid gap-4 sm:grid-cols-2"><CalendarWindowFields form={form} change={change} /></fieldset>
        <button className={buttonStyle} disabled={saving || busy}>{saving ? 'Saving…' : 'Save my calendar entry'}</button>
      </form>
    </details>
    <Message error>{error}</Message><Message>{message}</Message>
    <button className={secondaryStyle + ' mb-4'} disabled={busy || saving} onClick={refresh}>{busy ? 'Refreshing…' : 'Refresh availability'}</button>
    <CalendarConstraintList data={data} onCancel={cancel} busy={busy || saving} />
    <div className="mt-4"><Pagination data={data} busy={busy || saving} onPage={setOffset} /></div>
  </DashboardCard>
}
