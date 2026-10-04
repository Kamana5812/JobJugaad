import { useCallback, useEffect, useRef, useState } from 'react'
import { getOfferDocuments, offerDocumentErrorMessage } from '../api/offerDocuments'
import { Message, secondaryStyle } from './FormField'
import Pagination from './Pagination'
import { canUploadOfferDocument, formatFileSize } from './offerDocumentRules'
import OfferDocumentUpload from './OfferDocumentUpload'
import OfferDocumentRecord from './OfferDocumentRecord'

function DocumentsContent({ offer, admin, disabled, onSaved, onLockChange }) {
  const studentId = admin ? null : offer.student_id
  const [data, setData] = useState(null), [offset, setOffset] = useState(0), [busy, setBusy] = useState(false), [mutationLocked, setMutationLocked] = useState(false), [error, setError] = useState('')
  const request = useRef(0)
  const refresh = useCallback(async () => {
    const ticket = ++request.current; setBusy(true); setError('')
    try { const result = await getOfferDocuments(offer.id, studentId, offset); if (ticket === request.current) setData(result) }
    catch (failure) { if (ticket === request.current) setError(offerDocumentErrorMessage(failure)) }
    finally { if (ticket === request.current) setBusy(false) }
  }, [offer.id, offer.version, studentId, offset])
  useEffect(() => { refresh(); return () => { request.current++ } }, [refresh])
  function lock(value) { setMutationLocked(value); onLockChange(value) }
  async function saved(result) { await onSaved(result); await refresh() }
  const stale = data && data.offer_version !== offer.version
  const uploadAllowed = canUploadOfferDocument(offer, admin)
  return <div className="mt-4 space-y-4">
    <p className="text-sm text-muted">Earlier external declarations remain in stage history; they do not imply a stored file. File reviews and offer-stage decisions are manual. PDF format checks do not establish authenticity or provide antivirus scanning.</p>
    <button className={secondaryStyle} disabled={busy || mutationLocked} onClick={refresh}>{busy ? 'Loading files…' : 'Refresh private files'}</button><Message error>{error}</Message>
    {data && <><p className="text-sm text-muted">{data.explanation}</p><p className="text-xs text-muted">Retained storage: {data.limits.stored_files}/{data.limits.max_files} files · {formatFileSize(data.limits.stored_bytes)} of {formatFileSize(data.limits.max_offer_bytes)}. Superseded files count toward these limits.</p>
      {stale && <Message error>This offer changed. Refresh offers before uploading or reviewing files.</Message>}
      <OfferDocumentUpload offer={offer} admin={admin} data={data} stageAllowed={uploadAllowed} disabled={disabled || busy || stale || mutationLocked} onSaved={saved} onLockChange={lock} />
      {!uploadAllowed && <p className="text-xs text-muted">{admin ? 'Offer letter files can be added or replaced only while the letter stage is Draft.' : 'Supporting PDFs can be added while an issued, open offer has Documents Pending or Changes requested. Submission is a separate stage action.'}</p>}
      {data.total === 0 && <p className="text-sm text-muted">No private file records are available here yet.</p>}
      <div className="space-y-3">{data.items.map(file => <OfferDocumentRecord key={file.id} file={file} offer={offer} admin={admin} version={data.offer_version} disabled={disabled || busy || stale || mutationLocked} onSaved={saved} onLockChange={lock} />)}</div>
      <Pagination data={data} busy={busy || mutationLocked} onPage={setOffset} />
    </>}
  </div>
}

export default function OfferDocumentsPanel(props) {
  const [loaded, setLoaded] = useState(false)
  return <details className="mt-5 rounded-xl border border-line p-4" onToggle={event => { if (event.currentTarget.open) setLoaded(true) }}><summary className="cursor-pointer font-semibold text-navy">Private PDFs and human file review</summary>
    {loaded && <DocumentsContent {...props} />}
  </details>
}
