import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getAnalytics, getCalendar } from '../../api/admin'
import { errorMessage } from '../../api/student'
import { Message, secondaryStyle } from '../../components/FormField'
import AnalyticsPanel from './AnalyticsPanel'
import SchedulingPanel from './SchedulingPanel'
import SupportPanel from './SupportPanel'
import OffersPanel from './OffersPanel'
export default function AdminPage() {
  const { user } = useAuth()
  const [tab, setTab] = useState('overview')
  const [data, setData] = useState(null)
  const [board, setBoard] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const refresh = useCallback(async () => {
    const [nextData, nextBoard] = await Promise.all([getAnalytics(), getCalendar()])
    setData(nextData); setBoard(nextBoard)
  }, [])
  useEffect(() => { let active = true
    setBusy(true)
    refresh().catch(failure => { if (active) setError(errorMessage(failure)) }).finally(() => { if (active) setBusy(false) })
    return () => { active = false }
  }, [refresh])
  async function reload() {
    setBusy(true); setError('')
    try { await refresh() } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  return <div className="space-y-7">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">Explainability-first · Demo College {user.college_id}</p>
        <h1 className="mt-2 text-3xl font-bold text-navy sm:text-4xl">Placement Command Center</h1>
        <p className="mt-3 max-w-2xl text-muted">See the evidence. Plan a clear next step. Keep people in the decision.</p></div>
      <button className={secondaryStyle} onClick={reload} disabled={busy}>{busy ? 'Refreshing…' : 'Refresh dashboard'}</button>
    </header>
    <Message error>{error}</Message>
    <nav aria-label="Command Center sections" className="flex flex-wrap gap-2 rounded-2xl border border-line bg-white p-2">
      {[['overview', 'Overview'], ['scheduling', 'Scheduling' + (board?.conflicts.length ? ' · ' + board.conflicts.length + ' conflict(s)' : '')], ['support', 'Placement support'], ['offers', 'Offers']].map(([key, label]) =>
        <button key={key} onClick={() => setTab(key)} aria-current={tab === key ? 'page' : undefined}
          className={'rounded-xl px-5 py-3 text-sm font-bold ' + (tab === key ? 'bg-navy text-white' : 'text-navy hover:bg-paper')}>{label}</button>)}
    </nav>
    {!data || !board ? <p role="status">{busy ? 'Loading college records…' : 'Use Refresh dashboard to retry.'}</p> : <>
      {tab === 'overview' && <AnalyticsPanel data={data} />}
      {tab === 'scheduling' && <SchedulingPanel board={board} refresh={refresh} />}
      {tab === 'support' && <SupportPanel jobs={board.jobs} />}
      {tab === 'offers' && <OffersPanel refreshAnalytics={refresh} />}
    </>}
    <details className="rounded-2xl border border-line bg-white p-5 text-sm">
      <summary className="cursor-pointer font-bold text-navy">Jugaad Dost 🤝 · Quick help</summary>
      <div className="mt-4 space-y-3 text-muted"><p><strong>Who confirms a schedule?</strong> An administrator approves a proposal with a reason. Availability is checked again, so a stale proposal can be refused.</p>
        <p><strong>What do support indicators mean?</strong> They are proposed rule thresholds using recorded skills, self-reported interview scores and recent completed interview records. Review opportunity and missing records before acting.</p>
        <p><strong>What does placement percentage mean?</strong> It counts students with an issued, accepted offer, excluding recorded non-joining. Joining is reported separately. Synthetic offers are included and labeled; branch and skill charts still show shortlist conversion.</p>
        <p>This is a static help panel.</p></div>
    </details>
  </div>
}
