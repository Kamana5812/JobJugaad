import { useEffect, useState } from 'react'
import { FormField, buttonStyle, secondaryStyle, Message } from '../../components/FormField'
import DashboardCard, { displayTime, localInputTime } from '../../components/DashboardCard'
import { checkSlot, proposeSchedule } from '../../api/admin'
import { errorMessage } from '../../api/student'

export default function ScheduleForm({ board, source, onClearSource, onSaved }) {
  const initial = () => ({ job_id: board.jobs[0]?.id || '', student_id: board.students[0]?.id || '',
    scheduled_time: localInputTime(Date.now() + 86400000), duration_minutes: 30, venue: '', panel_id: '' })
  const [form, setForm] = useState(initial)
  const [preview, setPreview] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  useEffect(() => {
    if (source) setForm({ job_id: source.job_id, student_id: source.student_id,
      scheduled_time: localInputTime(Math.max(new Date(source.scheduled_time).getTime(), Date.now() + 3600000)),
      duration_minutes: (new Date(source.end_time) - new Date(source.scheduled_time)) / 60000,
      venue: source.venue, panel_id: source.panel_id })
    setPreview(null); setError(''); setMessage('')
  }, [source])
  const change = key => event => { setForm({ ...form, [key]: event.target.value }); setPreview(null); setMessage('') }
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('')
    const save = event.nativeEvent.submitter?.value === 'save'
    try {
      const input = { ...form, job_id: Number(form.job_id), student_id: Number(form.student_id),
        duration_minutes: Number(form.duration_minutes), scheduled_time: new Date(form.scheduled_time).toISOString(),
        reschedule_interview_id: source?.id || null }
      if (save) {
        const result = await proposeSchedule(input)
        setPreview(null)
        await onSaved()
        setMessage('Proposal #' + result.id + ' saved. Review and approve it below; the confirmed calendar has not changed.')
      } else setPreview(await checkSlot(input))
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <DashboardCard title={source ? 'Propose a new time for interview #' + source.id : '02 Propose an interview'} label="Availability → proposal → admin approval">
    <p className="mb-4 text-sm text-muted">Times use your browser timezone ({Intl.DateTimeFormat().resolvedOptions().timeZone}). The greedy checker skips occupied slots for up to seven days; campus working hours are not configured.</p>
    {source && <div className="mb-4 rounded-xl bg-paper p-3 text-sm"><p>The current booking stays in place until this proposal is approved.</p>
      <button type="button" className={secondaryStyle + ' mt-2'} onClick={onClearSource}>Switch to a new interview</button></div>}
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Drive" required value={form.job_id} onChange={change('job_id')} disabled={Boolean(source) || busy}>
          <option value="">Choose a drive</option>{board.jobs.map(job => <option key={job.id} value={job.id}>{job.name} (#{job.id})</option>)}</FormField>
        <FormField label="Student" required value={form.student_id} onChange={change('student_id')} disabled={Boolean(source) || busy}>
          <option value="">Choose a student</option>{board.students.map(student => <option key={student.id} value={student.id}>{student.name} (#{student.id})</option>)}</FormField>
        <FormField label="Requested start" type="datetime-local" required value={form.scheduled_time} onChange={change('scheduled_time')} />
        <FormField label="Duration (minutes)" type="number" min="5" max="240" step="1" required value={form.duration_minutes} onChange={change('duration_minutes')} />
        <FormField label="Venue" required maxLength="100" value={form.venue} onChange={change('venue')} hint="Use the same name for the same room." />
        <FormField label="Panel" required maxLength="80" value={form.panel_id} onChange={change('panel_id')} hint="Use the same name for the same interview panel." />
      </div>
      <Message error>{error}</Message><Message>{message}</Message>
      <div className="flex flex-wrap gap-3"><button className={secondaryStyle} disabled={busy} value="check">Check availability</button>
        <button className={buttonStyle} disabled={busy || !board.jobs.length || !board.students.length} value="save">{busy ? 'Checking…' : 'Create pending proposal'}</button></div>
    </form>
    {preview && <div className="mt-5 rounded-xl border border-line bg-paper p-4" role="status">
      <h3 className="font-bold text-navy">{preview.proposed_time ? 'Suggested: ' + displayTime(preview.proposed_time) + ' – ' + displayTime(preview.proposed_end_time) : 'No slot found'}</h3>
      <p className="mt-2 text-sm">{preview.explanation}</p>
      <ul className="mt-3 space-y-2 text-sm">{preview.conflicts.map(item => <li key={item.interview_id}>{item.explanation}</li>)}</ul>
      <p className="mt-3 text-xs text-muted">{preview.methodology} Availability is checked again when saving and approving.</p>
    </div>}
  </DashboardCard>
}
