import { useState } from 'react'
import CalendarWindowFields, { initialWindow, windowInput } from '../../components/CalendarWindowFields'
import { FormField, Message, buttonStyle } from '../../components/FormField'
import { createCalendarConstraint, calendarErrorMessage } from '../../api/calendar'

export default function CalendarConstraintForm({ students, onSaved }) {
  const [form, setForm] = useState(() => ({ ...initialWindow(), scope: 'student', student_id: students[0]?.id || '', resource_name: '', reason: '' }))
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('')
  const change = key => event => {
    const value = event.target.value
    setForm(current => ({ ...current, [key]: value, ...(key === 'kind' ? { scope: value === 'exam' ? 'campus' : 'student' } : {}) })); setMessage('')
  }
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('')
    let saved = false
    try {
      const dates = windowInput(form)
      if (form.reason.trim().length < 10) { setError('Enter a calendar reason with at least 10 non-space characters.'); return }
      await createCalendarConstraint({ ...dates, scope: form.scope, student_id: form.scope === 'student' ? Number(form.student_id) : null,
        resource_name: ['panel', 'branch'].includes(form.scope) ? form.resource_name.trim() : null, reason: form.reason.trim() })
      saved = true; setForm(current => ({ ...current, label: '', reason: '' })); await onSaved()
      setMessage('Calendar entry saved. Review existing booking alerts; pending proposals are checked again before approval.')
    } catch (failure) { setError(saved ? 'Entry saved, but the calendar could not refresh. Reload the calendar and dashboard.' : failure.isAxiosError ? calendarErrorMessage(failure) : failure.message) }
    finally { setBusy(false) }
  }
  return <form onSubmit={save} className="space-y-4">
    <p className="text-sm text-muted">Times use your browser timezone ({Intl.DateTimeFormat().resolvedOptions().timeZone}). With active Available entries, the entire interview must fit recorded windows for that student or panel. If no window fits the next seven days, no slot is proposed; cancel or replace outdated entries.</p>
    <fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2">
      <CalendarWindowFields form={form} change={change} exams />
      <FormField label="Applies to" value={form.scope} onChange={change('scope')}>
        {form.kind === 'exam' ? <><option value="campus">Entire college</option><option value="branch">One branch</option></> : <><option value="student">One student</option><option value="panel">One interview panel</option></>}
      </FormField>
      {form.scope === 'student' && <FormField label="Student for calendar entry" required value={form.student_id} onChange={change('student_id')}><option value="">Choose a student</option>{students.map(student => <option key={student.id} value={student.id}>{student.name} (#{student.id})</option>)}</FormField>}
      {['panel', 'branch'].includes(form.scope) && <FormField label={form.scope === 'panel' ? 'Panel name' : 'Branch name'} required maxLength="80" value={form.resource_name} onChange={change('resource_name')} hint={form.scope === 'panel' ? 'Use the same panel name as the interview proposal.' : 'Use the branch recorded on student profiles.'} />}
      <div className="sm:col-span-2"><FormField label="Reason for calendar entry" required minLength="10" maxLength="1000" value={form.reason} onChange={change('reason')} hint="At least 10 characters; avoid private exam or health details." /></div>
    </fieldset>
    <Message error>{error}</Message><Message>{message}</Message><button className={buttonStyle} disabled={busy}>{busy ? 'Saving…' : 'Add calendar entry'}</button>
  </form>
}
