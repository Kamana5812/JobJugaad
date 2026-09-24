import { useState } from 'react'
import { uploadResume, errorMessage } from '../api/student'
import { buttonStyle, Message } from './FormField'

export default function ResumeUpload({ sectionNumber = "02", profile, onUploaded, disabled, onExpired, onBusyChange }) {
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  async function upload(event) {
    event.preventDefault()
    setError(''); setMessage('')
    if (!file || file.size > 5 * 1024 * 1024) { setError('Choose a PDF no larger than 5 MB.'); return }
    setBusy(true); onBusyChange(true)
    try {
      const result = await uploadResume(profile.id, file)
      onUploaded(result.profile)
      setMessage(result.detail)
    } catch (failure) {
      if (failure.response?.status === 401) onExpired()
      else setError(errorMessage(failure))
    } finally { setBusy(false); onBusyChange(false) }
  }
  return <section className="rounded-3xl border border-line bg-white p-6 sm:p-8" aria-labelledby="resume-title">
    <h2 id="resume-title" className="text-xl font-bold text-navy"><span className="mr-3 text-saffron">{sectionNumber}</span>Your resume, readable.</h2>
    <p className="mt-2 text-sm leading-6 text-muted">PDF → Extracted text → Your review. Upload a text-based PDF, up to 5 MB and 20 pages. Use synthetic information in this public demo.</p>
    <form onSubmit={upload} className="mt-5 flex flex-wrap items-end gap-4">
      <label className="min-w-0 flex-1 text-sm font-semibold text-navy">Resume PDF
        <input type="file" accept=".pdf,application/pdf" required disabled={busy || disabled} className="mt-2 block w-full rounded-xl border border-line p-2.5 text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-paper file:px-3 file:py-2 file:font-semibold file:text-navy"
          onChange={(event) => { setFile(event.target.files?.[0] || null); setError(''); setMessage('') }} />
      </label>
      <button className={buttonStyle} disabled={busy || disabled || !file}>{busy ? 'Reading your PDF…' : 'Upload & extract text'}</button>
    </form>
    <div className="mt-4 space-y-2"><Message error>{error}</Message><Message>{message}</Message></div>
    <p className="mt-3 text-xs leading-5 text-muted">Extracted text does not automatically change your skills or readiness. Review it, then record accurate evidence below. Images and scanned PDFs are not read.</p>
    {profile.resume_text && <details className="mt-5 rounded-xl border border-line p-4"><summary className="cursor-pointer text-sm font-bold text-navy">Review saved resume text</summary>
      <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap break-words font-sans text-sm leading-6 text-ink">{profile.resume_text}</pre></details>}
  </section>
}
