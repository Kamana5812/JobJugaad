import { useEffect, useRef, useState } from 'react'
import { uploadOfferDocument, offerDocumentErrorMessage } from '../api/offerDocuments'
import { FormField, Message, buttonStyle } from './FormField'
import { canUploadOfferDocument, formatFileSize, uploadDocumentInput } from './offerDocumentRules'

export default function OfferDocumentUpload({ offer, admin, data, disabled, onSaved, onLockChange, stageAllowed = canUploadOfferDocument(offer, admin) }) {
  const kind = admin ? 'offer_letter' : 'supporting_document'
  const choices = data.items.filter(item => item.is_active && item.kind === kind)
  const [file, setFile] = useState(null), [form, setForm] = useState(() => ({ label: '', reason: '', replaces_document_id: admin ? choices[0]?.id || '' : '' }))
  const [busy, setBusy] = useState(false), [retry, setRetry] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('')
  const attempt = useRef(null), guard = useRef(false), picker = useRef(null)
  useEffect(() => {
    if (!attempt.current && admin) setForm(current => ({ ...current, replaces_document_id: choices[0]?.id || '' }))
  }, [data.items, admin])
  const change = key => event => { if (guard.current || attempt.current) return; setForm(current => ({ ...current, [key]: event.target.value })); setError(''); setMessage('') }
  async function submit(event) {
    event.preventDefault()
    if (guard.current || ((disabled || !stageAllowed) && !attempt.current)) return
    guard.current = true; setBusy(true); onLockChange(true); setError(''); setMessage('')
    try {
      if (!attempt.current) attempt.current = uploadDocumentInput(file, form, data.offer_version, data.limits, crypto.randomUUID())
      const result = await uploadOfferDocument(offer.id, admin ? null : offer.student_id, attempt.current)
      attempt.current = null; setRetry(false); setFile(null); if (picker.current) picker.current.value = ''
      setForm(current => ({ ...current, label: '', reason: '' }))
      setMessage('PDF #' + result.document.id + ' stored for human review. Uploading does not change any offer stage.')
      try { await onSaved(result) } catch { setError('The PDF was stored, but the offer/files could not refresh. Refresh offers before another action.') }
    } catch (failure) {
      if (!failure.isAxiosError || (failure.response?.status >= 400 && failure.response?.status < 500 && failure.response?.status !== 408)) {
        attempt.current = null; setRetry(false); setError(failure.isAxiosError ? offerDocumentErrorMessage(failure) : failure.message)
      } else { setRetry(true); setError(offerDocumentErrorMessage(failure) + ' Upload is not confirmed. Stay on this offers page and retry the same file; the original attempt will be reused.') }
    } finally { guard.current = false; setBusy(false); onLockChange(Boolean(attempt.current)) }
  }
  if (!stageAllowed && !attempt.current && !busy) return null
  return <form onSubmit={submit} className="mt-4 space-y-4 rounded-xl border border-line bg-paper p-4">
    <h4 className="font-semibold text-navy">{admin ? 'Upload a draft offer letter PDF' : 'Upload a supporting PDF'}</h4>
    <p className="text-xs leading-5 text-muted">Up to {formatFileSize(data.limits.max_bytes)} and {data.limits.max_pages} pages. Replacements keep earlier bytes and history. Issuance, document submission and verification remain separate human actions.</p>
    <fieldset disabled={busy || retry || disabled || !stageAllowed} className="grid gap-4 sm:grid-cols-2">
      <FormField label="File label" required minLength="3" maxLength="160" value={form.label} onChange={change('label')} />
      <FormField label="File to replace (optional)" value={form.replaces_document_id} onChange={change('replaces_document_id')}><option value="">Add a new file</option>{choices.map(item => <option key={item.id} value={item.id}>{item.label} (#{item.id})</option>)}</FormField>
      <label className="text-sm font-semibold text-navy sm:col-span-2">Private PDF<input ref={picker} type="file" accept=".pdf,application/pdf" required className="mt-2 block w-full rounded-lg border border-line bg-white p-2 text-sm" onChange={event => { if (!attempt.current) { setFile(event.target.files?.[0] || null); setError(''); setMessage('') } }} /></label>
      <div className="sm:col-span-2"><FormField label="Upload / replacement reason" required minLength="10" maxLength="1000" value={form.reason} onChange={change('reason')} hint="Recorded in file history. Include the purpose or correction; avoid unnecessary private details." /></div>
    </fieldset>
    <Message error>{error}</Message><Message>{message}</Message>
    {retry && <p className="text-xs text-muted">The draft is locked until this attempt is confirmed or refused. Changing offer pages, navigating away, or reloading loses its retry identifier; collapsing this panel preserves it.</p>}
    <button className={buttonStyle} disabled={busy || ((disabled || !stageAllowed) && !retry) || (!retry && !file)}>{busy ? 'Storing PDF…' : retry ? 'Retry the same upload' : 'Store private PDF'}</button>
  </form>
}
