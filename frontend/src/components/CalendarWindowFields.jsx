import { FormField } from './FormField'
import { localInputTime } from './DashboardCard'

export function initialWindow() {
  const start = Date.now() + 86400000
  return { kind: 'available', starts_at: localInputTime(start), ends_at: localInputTime(start + 3600000), label: '' }
}

export function windowInput(form) {
  const start = new Date(form.starts_at), end = new Date(form.ends_at)
  if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || end <= start) {
    throw new Error('Choose a valid end time later than the start time.')
  }
  if (form.label.trim().length < 3) throw new Error('Enter a calendar label with at least 3 characters.')
  return { kind: form.kind, starts_at: start.toISOString(), ends_at: end.toISOString(), label: form.label.trim() }
}

export default function CalendarWindowFields({ form, change, exams = false }) {
  return <>
    <FormField label="Entry type" value={form.kind} onChange={change('kind')}>
      <option value="available">Available</option><option value="unavailable">Unavailable</option>
      {exams && <option value="exam">Exam block</option>}
    </FormField>
    <FormField label="Calendar label" required minLength="3" maxLength="160" value={form.label} onChange={change('label')} hint="Use a short label without private or sensitive details." />
    <FormField label="Starts at" type="datetime-local" required value={form.starts_at} onChange={change('starts_at')} />
    <FormField label="Ends at" type="datetime-local" required value={form.ends_at} onChange={change('ends_at')} />
  </>
}
