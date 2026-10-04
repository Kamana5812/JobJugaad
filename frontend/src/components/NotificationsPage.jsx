import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import { getNotifications, readNotification } from '../api/notifications'
import { errorMessage } from '../api/student'
import DashboardCard, { displayTime } from './DashboardCard'
import Pagination from './Pagination'
import { Message, secondaryStyle } from './FormField'

export function NotificationItem({ item, busy, onRead }) {
  const kindLabel = item.kind === 'drive_update' ? 'Drive update' : item.kind === 'drive_reminder' ? 'Manual drive reminder' : ''
  return <DashboardCard title={item.title} label={(item.read_at ? 'Read' : 'Unread') + (kindLabel ? ' · ' + kindLabel : '')}>
    <p className="whitespace-pre-wrap break-words text-sm">{item.body}</p><p className="mt-2 text-xs text-muted">{displayTime(item.created_at)}</p>
    <div className="mt-4 flex flex-wrap gap-4">{['/admin', '/student/offers', '/notifications', '/auth', '/student#applications', '/recruiter#applications'].includes(item.target_path) && <Link className="text-sm font-bold text-navy underline" to={item.target_path}>Open related page</Link>}
      {!item.read_at && <button className={secondaryStyle} disabled={busy} onClick={() => onRead(item.id)}>Mark as read</button>}</div>
  </DashboardCard>
}
export default function NotificationsPage() {
  const { user } = useAuth()
  const demo = [1, 2].includes(user.college_id)
  const [data, setData] = useState(null)
  const [offset, setOffset] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const refresh = useCallback(async () => {
    setBusy(true); setError('')
    try { setData(await getNotifications(offset)) } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }, [offset])
  useEffect(() => { refresh() }, [refresh])
  async function markRead(id) {
    setBusy(true); setError('')
    try { await readNotification(id); await refresh() } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  return <div className="space-y-5">
    <header><p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">{demo ? 'Archived demo feed' : 'In-app feed'}</p><h1 className="mt-2 text-3xl font-bold text-navy">Notifications</h1><p className="mt-3 text-muted">Hiring updates appear here; they are not delivered by email or SMS. {data && `${data.unread_count} unread notification(s).`}</p></header>
    <button className={secondaryStyle} disabled={busy} onClick={refresh}>Refresh feed</button><Message error>{error}</Message>
    {busy && <p role="status">Updating feed…</p>}{data?.total === 0 && <p>No notifications yet. Drive announcements, interview and offer updates will appear here.</p>}
    {data?.notifications.map(item => <NotificationItem key={item.id} item={item} busy={busy} onRead={markRead} />)}
    <Pagination data={data} busy={busy} onPage={setOffset} />
  </div>
}
