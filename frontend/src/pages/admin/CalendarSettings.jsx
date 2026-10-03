import { useCallback, useEffect, useState } from 'react'
import { getCalendarSettings, saveCalendarSettings, calendarErrorMessage } from '../../api/calendar'
import DashboardCard from '../../components/DashboardCard'
import { FormField, Message, buttonStyle, secondaryStyle } from '../../components/FormField'

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
export default function CalendarSettings({ onChanged }) {
  const [form, setForm] = useState(null), [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('')
  const load = useCallback(async () => {
    setBusy(true); setError('')
    try { setForm(await getCalendarSettings()) } catch (failure) { setError(calendarErrorMessage(failure)) }
    finally { setBusy(false) }
  }, [])
  useEffect(() => { load() }, [load])
  const change = key => event => { setForm({ ...form, [key]: event.target.value }); setMessage('') }
  function toggle(key) { setForm({ ...form, [key]: !form[key] }); setMessage('') }
  function toggleDay(index) {
    setForm({ ...form, weekdays: form.weekdays.includes(index) ? form.weekdays.filter(day => day !== index) : [...form.weekdays, index].sort() }); setMessage('')
  }
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('')
    let saved = false
    try {
      if (!form.weekdays.length) { setError('Choose at least one working weekday.'); return }
      if (form.day_start >= form.day_end) { setError('Day ends must be later than day starts; overnight hours are not supported.'); return }
      if (reason.trim().length < 10) { setError('Enter a change reason with at least 10 non-space characters.'); return }
      const { college_id, ...settings } = form
      setForm(await saveCalendarSettings({ ...settings, reason: reason.trim() })); saved = true; setReason('')
      await onChanged()
      setMessage('Calendar rules saved. Existing bookings remain scheduled; review any calendar alerts below.')
    } catch (failure) { setError(saved ? 'Rules saved, but the booking list could not refresh. Click Refresh dashboard.' : calendarErrorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <DashboardCard title="Campus calendar rules" label="College-scoped policy · administrator review">
    <p className="mb-4 text-sm text-muted">The working-hours switch affects campus hours only. Dated unavailability and exam blocks apply independently. Required availability uses the recorded student or panel windows.</p>
    <Message error>{error}</Message><Message>{message}</Message>
    {!form ? <button className={secondaryStyle} disabled={busy} onClick={load}>{busy ? 'Loading rules…' : 'Retry calendar rules'}</button> : <form onSubmit={save} className="mt-4 space-y-4">
      <fieldset disabled={busy} className="space-y-4">
        <label className="flex items-start gap-3 text-sm text-navy"><input type="checkbox" className="mt-1 accent-navy" checked={form.enabled} onChange={() => toggle('enabled')} /><span className="font-semibold">Enforce campus working hours</span></label>
        <div className="grid gap-4 sm:grid-cols-3">
          <FormField label="Campus timezone" required maxLength="80" value={form.timezone} onChange={change('timezone')} hint="IANA name, for example Asia/Kolkata." />
          <FormField label="Day starts" type="time" required value={form.day_start} onChange={change('day_start')} />
          <FormField label="Day ends" type="time" required value={form.day_end} onChange={change('day_end')} />
        </div>
        <fieldset className="rounded-lg border border-line p-3"><legend className="px-1 text-sm font-semibold text-navy">Working weekdays</legend>
          <div className="flex flex-wrap gap-x-5 gap-y-3">{days.map((day, index) => <label key={day} className="flex items-center gap-2 text-sm"><input type="checkbox" className="accent-navy" checked={form.weekdays.includes(index)} onChange={() => toggleDay(index)} />{day}</label>)}</div>
        </fieldset>
        <div className="space-y-3 text-sm">
          <label className="flex items-start gap-3"><input type="checkbox" className="mt-1 accent-navy" checked={form.require_student_availability} onChange={() => toggle('require_student_availability')} /><span>Require a recorded available window for every student booking</span></label>
          <label className="flex items-start gap-3"><input type="checkbox" className="mt-1 accent-navy" checked={form.require_panel_availability} onChange={() => toggle('require_panel_availability')} /><span>Require a recorded available window for every panel booking</span></label>
          <p className="text-xs text-muted">These requirements apply even when working hours are off. Without a suitable available window, the checker cannot propose a slot.</p>
        </div>
        <FormField label="Reason for calendar rule change" required minLength="10" maxLength="1000" value={reason} onChange={event => setReason(event.target.value)} hint="At least 10 characters; recorded in the calendar audit history." />
      </fieldset>
      <div className="flex flex-wrap items-center gap-3"><button className={buttonStyle} disabled={busy}>{busy ? 'Saving…' : 'Save calendar rules'}</button><button type="button" className={secondaryStyle} disabled={busy} onClick={load}>Reload saved rules</button><span className="text-xs text-muted">Saved version {form.version}</span></div>
    </form>}
  </DashboardCard>
}
