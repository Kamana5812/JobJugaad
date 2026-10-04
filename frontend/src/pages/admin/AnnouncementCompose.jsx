import { useId, useRef, useState } from 'react'
import { previewAnnouncement, publishAnnouncement, announcementErrorMessage } from '../../api/announcements'
import { FormField, Message, inputStyle, secondaryStyle } from '../../components/FormField'
import AnnouncementPreview from './AnnouncementPreview'

export function announcementInput(form) {
  const input = { job_id: Number(form.job_id), audience: form.audience, branch: form.branch?.trim().replace(/\s+/g, ' ').toUpperCase() || null,
    kind: form.kind, title: form.title.trim(), body: form.body.trim() }
  if (!Number.isInteger(input.job_id) || input.job_id <= 0) throw new Error('Choose a drive before previewing.')
  if (input.title.length < 3) throw new Error('Enter a title with at least 3 characters.')
  if (input.body.length < 10) throw new Error('Enter a message with at least 10 characters.')
  return input
}

export function publicationInput(preview, key) {
  return { ...announcementInput(preview), preview_hash: preview.preview_hash, idempotency_key: key }
}

export default function AnnouncementCompose({ options, onPublished, onLockChange = () => {} }) {
  const bodyId = useId()
  const [form, setForm] = useState(() => ({ job_id: options.jobs[0]?.id || '', audience: 'applicants', branch: '', kind: 'update', title: '', body: '' }))
  const [preview, setPreview] = useState(null), [reviewed, setReviewed] = useState(false), [busy, setBusy] = useState(false)
  const [error, setError] = useState(''), [message, setMessage] = useState(''), [retry, setRetry] = useState(false)
  const guard = useRef(false), publicationKey = useRef(null), reviewConfirmed = useRef(false), retainedAttempt = useRef(false)
  function invalidate() { setPreview(null); setReviewed(false); reviewConfirmed.current = false; publicationKey.current = null; retainedAttempt.current = false; setRetry(false) }
  const change = key => event => { if (guard.current || retainedAttempt.current) return; setForm(current => ({ ...current, [key]: event.target.value })); invalidate(); setError(''); setMessage('') }
  async function prepare(event) {
    event.preventDefault()
    if (guard.current || retainedAttempt.current) return
    guard.current = true; setBusy(true); onLockChange(true); setError(''); setMessage(''); invalidate()
    try { const result = await previewAnnouncement(announcementInput(form)); setPreview(result); publicationKey.current = crypto.randomUUID() }
    catch (failure) { setError(failure.isAxiosError ? announcementErrorMessage(failure) : failure.message) }
    finally { guard.current = false; setBusy(false); onLockChange(false) }
  }
  async function publish() {
    if (guard.current || !preview || !publicationKey.current || !reviewConfirmed.current || preview.recipient_count === 0) return
    guard.current = true; setBusy(true); onLockChange(true); setError(''); setMessage('')
    try {
      const result = await publishAnnouncement(publicationInput(preview, publicationKey.current))
      invalidate(); setForm(current => ({ ...current, title: '', body: '' }))
      setMessage('Announcement #' + result.id + ' published in-app to ' + result.recipient_count + ' student(s).')
      try { await onPublished(result) } catch { setError('Announcement #' + result.id + ' was published, but history could not refresh. Use Refresh history and read counts.') }
    } catch (failure) {
      if (failure.response?.status === 409) { invalidate(); setError(announcementErrorMessage(failure) + ' Preview the current audience again before publishing.') }
      else if (failure.response?.status >= 400 && failure.response?.status < 500 && failure.response?.status !== 408) {
        invalidate(); setError(announcementErrorMessage(failure) + (failure.response.status === 401 ? ' Sign in again before previewing.' : ' Review the draft or account access, then preview again before publishing.'))
      }
      else { retainedAttempt.current = true; setRetry(true); setError(announcementErrorMessage(failure) + ' Publication is not confirmed. Retry the same publication without changing the draft; duplicate copies will not be created for that attempt.') }
    } finally { guard.current = false; setBusy(false); onLockChange(retainedAttempt.current) }
  }
  return <div className="space-y-4">
    <form onSubmit={prepare} className="space-y-4">
      <fieldset disabled={busy || retry} className="grid gap-4 sm:grid-cols-2">
        <FormField label="Announcement drive" required value={form.job_id} onChange={change('job_id')}><option value="">Choose a drive</option>{options.jobs.map(job => <option key={job.id} value={job.id}>{job.name} (#{job.id})</option>)}</FormField>
        <FormField label="Student audience" value={form.audience} onChange={change('audience')}><option value="applicants">Drive applicants</option><option value="shortlisted">Recorded shortlisted students</option><option value="scheduled">Students with recorded scheduled interviews</option><option value="college_students">College students</option></FormField>
        <FormField label="Branch filter" value={form.branch} onChange={change('branch')}><option value="">All branches in this audience</option>{options.branches.map(branch => <option key={branch} value={branch}>{branch}</option>)}</FormField>
        <FormField label="Message type" value={form.kind} onChange={change('kind')}><option value="update">Drive update</option><option value="reminder">Manual reminder</option></FormField>
        <div className="sm:col-span-2"><FormField label="Announcement title" required minLength="3" maxLength="160" value={form.title} onChange={change('title')} /></div>
        <div className="sm:col-span-2"><label htmlFor={bodyId} className="mb-1.5 block text-sm font-semibold text-navy">Message</label><textarea id={bodyId} aria-describedby={bodyId + '-hint'} className={inputStyle + ' min-h-32'} required minLength="10" maxLength="4000" value={form.body} onChange={change('body')} /><p id={bodyId + '-hint'} className="mt-1.5 text-xs text-muted">Plain text only. Keep private details out of group updates. Reminders are published manually, not scheduled.</p></div>
      </fieldset>
      <button className={secondaryStyle} disabled={busy || retry || !options.jobs.length}>{busy ? 'Working…' : 'Preview audience'}</button>
    </form>
    <Message error>{error}</Message><Message>{message}</Message>
    {retry && <p className="text-sm text-muted">Keep this draft open and retry the same publication to resolve its status. Message fields stay locked while the result is uncertain.</p>}
    {preview && <AnnouncementPreview preview={preview} reviewed={reviewed} onReviewed={value => { reviewConfirmed.current = value; setReviewed(value) }} onPublish={publish} busy={busy} retry={retry} />}
  </div>
}
