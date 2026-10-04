import { useRef, useState } from 'react'
import { downloadOfferDocument, offerDocumentErrorMessage, saveDownloadedPdf } from '../api/offerDocuments'
import { displayTime, StatusPill } from './DashboardCard'
import { Message, secondaryStyle } from './FormField'
import { canReviewOfferDocument, formatFileSize, studentLetterAvailable } from './offerDocumentRules'
import OfferDocumentEvents from './OfferDocumentEvents'
import OfferDocumentReview from './OfferDocumentReview'

export default function OfferDocumentRecord({ file, offer, admin, version, disabled, onSaved, onLockChange }) {
  const [expanded, setExpanded] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const guard = useRef(false), studentId = admin ? null : offer.student_id
  if (!admin && file.kind === 'offer_letter' && !studentLetterAvailable(offer)) return null
  async function download() {
    if (guard.current) return
    guard.current = true; setBusy(true); setError('')
    try { saveDownloadedPdf(await downloadOfferDocument(offer.id, file.id, studentId), offer.id, file.id) }
    catch (failure) { setError(offerDocumentErrorMessage(failure)) }
    finally { guard.current = false; setBusy(false) }
  }
  return <article className="rounded-xl border border-line p-4">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h4 className="break-words font-semibold text-navy">{file.label}</h4><p className="mt-1 text-xs text-muted">{file.kind === 'offer_letter' ? 'Offer letter PDF' : 'Supporting PDF'} · File #{file.id}</p></div><StatusPill warning={!file.is_active}>{file.is_active ? 'Current file' : 'Superseded file'}</StatusPill></div>
    <p className="mt-3 break-words text-sm">{file.original_filename} · {formatFileSize(file.size_bytes)} · {file.page_count} page(s)</p>
    <p className="mt-1 text-xs text-muted">Uploaded {displayTime(file.uploaded_at)} · Account #{file.uploaded_by}{file.supersedes_document_id && ' · Replaces file #' + file.supersedes_document_id}</p>
    <div className="mt-3"><StatusPill warning={file.review_status === 'pending'} critical={file.review_status === 'rejected'}>Human file review: {file.review_status}</StatusPill></div>
    {file.reviewed_at && <><p className="mt-2 text-xs text-muted">Reviewed {displayTime(file.reviewed_at)} · Account #{file.reviewed_by}</p><p className="mt-1 whitespace-pre-wrap break-words text-sm">{file.review_reason}</p></>}
    {file.kind === 'offer_letter' && offer.offer_letter_status === 'draft' && <p className="mt-2 text-xs text-muted">Draft letter file. It has not been issued; issuance remains an explicit offer-stage action.</p>}
    <button type="button" className={secondaryStyle + ' mt-3'} disabled={busy} onClick={download}>{busy ? 'Downloading…' : 'Download private PDF #' + file.id}</button><div className="mt-3"><Message error>{error}</Message></div>
    {canReviewOfferDocument(file, offer, admin) && <OfferDocumentReview offerId={offer.id} documentId={file.id} version={version} disabled={disabled} onSaved={onSaved} onLockChange={onLockChange} />}
    <details className="mt-4 text-sm" onToggle={event => setExpanded(event.currentTarget.open)}><summary className="cursor-pointer font-semibold text-navy">File history and checksum</summary><p className="mt-3 break-all text-xs text-muted">SHA-256: {file.sha256}</p>{expanded && <OfferDocumentEvents offerId={offer.id} documentId={file.id} studentId={studentId} />}</details>
  </article>
}
