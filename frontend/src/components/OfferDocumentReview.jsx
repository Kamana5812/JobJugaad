import { useRef, useState } from 'react'
import { reviewOfferDocument, offerDocumentErrorMessage } from '../api/offerDocuments'
import { FormField, Message, buttonStyle } from './FormField'

export default function OfferDocumentReview({ offerId, documentId, version, disabled, onSaved, onLockChange }) {
  const [status, setStatus] = useState('verified'), [reason, setReason] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('')
  const guard = useRef(false)
  async function submit(event) {
    event.preventDefault()
    if (guard.current || disabled) return
    if (reason.trim().length < 10) { setError('Enter a review reason with at least 10 characters.'); return }
    guard.current = true; setBusy(true); onLockChange(true); setError(''); setMessage('')
    try {
      const result = await reviewOfferDocument(offerId, documentId, { version, review_status: status, reason: reason.trim() })
      setReason(''); setMessage('Human file review recorded. Overall offer verification remains a separate action.')
      try { await onSaved(result) } catch { setError('The review was saved, but the offer/files could not refresh. Refresh offers before another action.') }
    } catch (failure) { setError(offerDocumentErrorMessage(failure) + ' Refresh offers and files before trying another review.') }
    finally { guard.current = false; setBusy(false); onLockChange(false) }
  }
  return <form onSubmit={submit} className="mt-4 space-y-3 rounded-lg bg-paper p-3">
    <fieldset disabled={busy || disabled} className="space-y-3">
      <FormField label={'Human review for file #' + documentId} value={status} onChange={event => setStatus(event.target.value)}><option value="verified">Record file verified by human review</option><option value="rejected">Record file rejected by human review</option></FormField>
      <FormField label={'Review reason for file #' + documentId} required minLength="10" maxLength="1000" value={reason} onChange={event => setReason(event.target.value)} hint="Record what you checked or the corrections required. JobJugaad does not verify authenticity automatically." />
    </fieldset>
    <Message error>{error}</Message><Message>{message}</Message><button className={buttonStyle} disabled={busy || disabled}>{busy ? 'Saving review…' : 'Record human file review'}</button>
  </form>
}
