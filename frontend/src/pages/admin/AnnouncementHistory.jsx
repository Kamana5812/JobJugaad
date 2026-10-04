import { useCallback, useEffect, useRef, useState } from 'react'
import { getAnnouncements, announcementErrorMessage } from '../../api/announcements'
import DashboardCard, { displayTime } from '../../components/DashboardCard'
import { Message, secondaryStyle } from '../../components/FormField'
import Pagination from '../../components/Pagination'
import AnnouncementRecipients from './AnnouncementRecipients'

export function AnnouncementRecord({ item }) {
  const [expanded, setExpanded] = useState(false)
  return <article className="rounded-xl border border-line p-4">
    <p className="text-xs font-semibold uppercase tracking-wide text-saffron-deep">{item.kind === 'reminder' ? 'Manual reminder' : 'Drive update'} · #{item.id}</p>
    <h3 className="mt-2 break-words font-semibold text-navy">{item.title}</h3><p className="mt-1 text-sm text-muted">{item.job_title} · {item.company_name}{item.branch && ' · Branch: ' + item.branch}</p>
    <p className="mt-3 whitespace-pre-wrap break-words text-sm">{item.body}</p>
    <p className="mt-3 text-xs text-muted">Published {displayTime(item.published_at)} · Administrator #{item.published_by} · {item.recipient_count} recorded recipient(s) · {item.read_count} read in-app</p>
    <p className="mt-2 text-sm text-muted">{item.explanation}</p>
    <details className="mt-4 text-sm" onToggle={event => setExpanded(event.currentTarget.open)}><summary className="cursor-pointer font-semibold text-navy">Recorded recipients and read status</summary>{expanded && <AnnouncementRecipients announcementId={item.id} />}</details>
  </article>
}

export default function AnnouncementHistory() {
  const [data, setData] = useState(null), [offset, setOffset] = useState(0), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const request = useRef(0)
  const refresh = useCallback(async () => {
    const ticket = ++request.current; setBusy(true); setError('')
    try { const result = await getAnnouncements(offset); if (ticket === request.current) setData(result) }
    catch (failure) { if (ticket === request.current) setError(announcementErrorMessage(failure)) }
    finally { if (ticket === request.current) setBusy(false) }
  }, [offset])
  useEffect(() => { refresh(); return () => { request.current++ } }, [refresh])
  return <DashboardCard title="Published announcement history" label="Recorded message and audience · current read counts">
    <p className="mb-4 text-sm text-muted">Published messages cannot be edited or deleted here. Publish a new update to correct earlier information. Read counts indicate in-app reads, not email delivery or attendance.</p>
    <button className={secondaryStyle + ' mb-4'} disabled={busy} onClick={refresh}>{busy ? 'Refreshing…' : 'Refresh history and read counts'}</button><Message error>{error}</Message>
    {data?.total === 0 && <p className="text-sm text-muted">No drive announcements published yet.</p>}
    <div className="space-y-4">{data?.items.map(item => <AnnouncementRecord key={item.id} item={item} />)}</div>
    <div className="mt-4"><Pagination data={data} busy={busy} onPage={setOffset} /></div>
  </DashboardCard>
}
