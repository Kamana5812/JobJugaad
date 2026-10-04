import { useCallback, useEffect, useRef, useState } from 'react'
import { getOfferDocumentEvents, offerDocumentErrorMessage } from '../api/offerDocuments'
import { displayTime } from './DashboardCard'
import { Message, secondaryStyle } from './FormField'
import Pagination from './Pagination'

export default function OfferDocumentEvents({ offerId, documentId, studentId }) {
  const [data, setData] = useState(null), [offset, setOffset] = useState(0), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const request = useRef(0)
  const refresh = useCallback(async () => {
    const ticket = ++request.current; setBusy(true); setError('')
    try { const result = await getOfferDocumentEvents(offerId, documentId, studentId, offset); if (ticket === request.current) setData(result) }
    catch (failure) { if (ticket === request.current) setError(offerDocumentErrorMessage(failure)) }
    finally { if (ticket === request.current) setBusy(false) }
  }, [offerId, documentId, studentId, offset])
  useEffect(() => { refresh(); return () => { request.current++ } }, [refresh])
  return <div className="mt-3 space-y-3">
    <button className={secondaryStyle} disabled={busy} onClick={refresh}>{busy ? 'Refreshing…' : 'Refresh file history'}</button><Message error>{error}</Message>
    {data && <p className="text-xs text-muted">{data.explanation}</p>}
    <ol className="space-y-3">{data?.items.map(event => <li key={event.id} className="border-t border-line pt-3 text-sm"><p className="font-semibold text-navy">{event.action.replaceAll('_', ' ')} · Account #{event.actor_user_id}</p><p className="mt-1 text-xs text-muted">{displayTime(event.created_at)}</p><p className="mt-2 whitespace-pre-wrap break-words">{event.reason}</p></li>)}</ol>
    <Pagination data={data} busy={busy} onPage={setOffset} />
  </div>
}
