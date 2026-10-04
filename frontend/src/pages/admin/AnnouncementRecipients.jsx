import { useCallback, useEffect, useRef, useState } from 'react'
import { getAnnouncementRecipients, announcementErrorMessage } from '../../api/announcements'
import { displayTime } from '../../components/DashboardCard'
import { Message, secondaryStyle } from '../../components/FormField'
import Pagination from '../../components/Pagination'

export default function AnnouncementRecipients({ announcementId }) {
  const [data, setData] = useState(null), [offset, setOffset] = useState(0), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const request = useRef(0)
  const refresh = useCallback(async () => {
    const ticket = ++request.current; setBusy(true); setError('')
    try { const result = await getAnnouncementRecipients(announcementId, offset); if (ticket === request.current) setData(result) }
    catch (failure) { if (ticket === request.current) setError(announcementErrorMessage(failure)) }
    finally { if (ticket === request.current) setBusy(false) }
  }, [announcementId, offset])
  useEffect(() => { refresh(); return () => { request.current++ } }, [refresh])
  return <div className="mt-4 space-y-3">
    <p className="text-xs text-muted">Names and branches are recorded at publication. Read status reflects the latest refresh of each recipient’s in-app copy.</p>
    <button className={secondaryStyle} disabled={busy} onClick={refresh}>{busy ? 'Refreshing…' : 'Refresh recipient read status'}</button><Message error>{error}</Message>
    {data && <p className="text-sm text-muted">{data.explanation}</p>}
    {data?.total === 0 && <p className="text-sm text-muted">No recorded recipients.</p>}
    <ul className="divide-y divide-line">{data?.items.map(item => <li key={item.notification_id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"><span>{item.name} · {item.branch} · Student #{item.student_id}</span><span className="text-muted">{item.read_at ? 'Read ' + displayTime(item.read_at) : 'Unread'}</span></li>)}</ul>
    <Pagination data={data} busy={busy} onPage={setOffset} />
  </div>
}
