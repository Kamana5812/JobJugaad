import { useCallback, useEffect, useState } from 'react'
import { getInterviews, errorMessage } from '../../api/student'
import DashboardCard, { displayTime } from '../../components/DashboardCard'
import Pagination from '../../components/Pagination'
import { Message, secondaryStyle } from '../../components/FormField'
import AvailabilityPanel from './AvailabilityPanel'
export default function InterviewsPanel({ studentId }) {
  const [data, setData] = useState(null), [offset, setOffset] = useState(0), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const refresh = useCallback(async () => { setBusy(true); setError(''); try { setData(await getInterviews(studentId, offset)) } catch(e) { setError(errorMessage(e)) } finally { setBusy(false) } }, [studentId, offset])
  useEffect(() => { refresh() }, [refresh])
  return <section id="interviews" className="space-y-4"><h2 className="text-xl font-semibold text-navy">My interviews</h2><p className="text-sm text-muted">Confirmed bookings and recorded outcomes. Pending proposals are not bookings; selected does not mean an offer.</p><button className={secondaryStyle} disabled={busy} onClick={refresh}>Refresh interviews</button><Message error>{error}</Message>
    {data?.total === 0 && <p className="text-sm text-muted">No interviews recorded yet. After recruiter shortlisting, your college administrator can propose and approve a booking.</p>}
    {data?.items.map(item => <DashboardCard key={item.id} title={item.job_title} label={item.status}><p className="text-sm">{item.company_name}</p><p className="mt-1 text-sm text-muted">Round {item.round_number || 1} · {item.round_name || 'Interview'}</p><p className="mt-2 text-sm">{displayTime(item.scheduled_time)} – {displayTime(item.end_time)}</p><p className="mt-2 text-sm text-muted">Venue: {item.venue} · Panel: {item.panel_id}</p></DashboardCard>)}<Pagination data={data} busy={busy} onPage={setOffset} />
    <AvailabilityPanel studentId={studentId} />
  </section>
}
