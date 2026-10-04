import { buttonStyle } from '../../components/FormField'

export default function AnnouncementPreview({ preview, reviewed, onReviewed, onPublish, busy, retry }) {
  return <section className="mt-5 rounded-xl border border-line bg-paper p-4" aria-label="Announcement publication preview">
    <h3 className="font-semibold text-navy">Review before publication</h3>
    <p className="mt-2 text-sm">{preview.job_title} · {preview.company_name}{preview.branch && ' · Branch: ' + preview.branch}</p>
    <p className="mt-3 text-lg font-semibold text-navy">{preview.recipient_count} student recipient(s)</p>
    <p className="mt-2 text-sm text-muted">{preview.explanation}</p>
    <div className="mt-4 rounded-lg border border-line bg-white p-4"><p className="break-words font-semibold text-navy">{preview.title}</p><p className="mt-2 whitespace-pre-wrap break-words text-sm">{preview.body}</p></div>
    {preview.sample.length > 0 && <details className="mt-4 text-sm"><summary className="cursor-pointer font-semibold text-navy">Recipient sample ({preview.sample.length} of {preview.recipient_count})</summary>
      <ul className="mt-2 space-y-2">{preview.sample.map(student => <li key={student.student_id}>{student.name} · {student.branch} · Student #{student.student_id}</li>)}</ul>
    </details>}
    {preview.recipient_count === 0 ? <p className="mt-4 text-sm text-muted">No recipients currently match this audience. Change the targeting and preview again.</p> : <label className="mt-4 flex items-start gap-3 text-sm"><input type="checkbox" checked={reviewed} onChange={event => onReviewed(event.target.checked)} disabled={busy} className="mt-1 accent-navy" /><span>I reviewed the message, audience and recipient count ({preview.recipient_count}). Publish an in-app copy for each.</span></label>}
    <p className="mt-3 text-xs text-muted">This publishes now. No email, SMS or scheduled delivery is sent. Published text and recipient identities remain in history; corrections require a new update.</p>
    <button type="button" onClick={onPublish} disabled={busy || !reviewed || preview.recipient_count === 0} className={buttonStyle + ' mt-4'}>{busy ? 'Publishing…' : retry ? 'Retry the same publication' : 'Publish to ' + preview.recipient_count + ' student(s)'}</button>
  </section>
}
