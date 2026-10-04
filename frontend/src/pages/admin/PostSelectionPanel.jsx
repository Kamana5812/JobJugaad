import { useCallback, useEffect, useRef, useState } from 'react'
import { getPostSelection, postSelectionErrorMessage } from '../../api/postSelection'
import DashboardCard from '../../components/DashboardCard'
import { FormField, Message, secondaryStyle } from '../../components/FormField'
import PostSelectionContent from './PostSelectionContent'

export default function PostSelectionPanel({ refreshKey }) {
  const [scope, setScope] = useState('recorded'), [job, setJob] = useState(''), [offset, setOffset] = useState(0)
  const [data, setData] = useState(null), [drives, setDrives] = useState([]), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const request = useRef(0)
  const refresh = useCallback(async () => {
    const ticket = ++request.current; setBusy(true); setError(''); setData(null)
    try {
      const result = await getPostSelection({ scope, job_id: job, offset })
      if (ticket === request.current) { setData(result); setDrives(result.drives) }
    } catch (failure) { if (ticket === request.current) setError(postSelectionErrorMessage(failure)) }
    finally { if (ticket === request.current) setBusy(false) }
  }, [scope, job, offset])
  useEffect(() => { refresh(); return () => { request.current++ } }, [refresh, refreshKey])
  const change = setter => event => { request.current++; setData(null); setError(''); setOffset(0); setter(event.target.value) }
  return <DashboardCard title="05 Post-selection journey" label="Recorded milestones · student–drive pairs">
    <p className="mb-4 text-sm leading-6 text-muted">Follow selection through joining, with recorded closure reasons. A student in two drives counts as two pairs; interview rounds do not add extra pairs. These are workflow records, not independently verified employment or predictions.</p>
    <div className="mb-4 grid gap-4 sm:grid-cols-2">
      <FormField label="Journey records" value={scope} onChange={change(setScope)}>
        <option value="recorded">Recorded college workflow</option><option value="synthetic">Synthetic and archived demo workflow</option><option value="all">All recorded workflow</option>
      </FormField>
      <FormField label="Journey drive" value={job} onChange={change(setJob)}>
        <option value="">All college drives</option>{drives.map(drive => <option key={drive.id} value={drive.id}>{drive.title} (#{drive.id})</option>)}
      </FormField>
    </div>
    <button type="button" className={secondaryStyle + ' mb-4'} disabled={busy} onClick={refresh}>{busy ? 'Loading journey…' : 'Refresh journey and reasons'}</button>
    <Message error>{error}</Message>
    {!data && !error && <p role="status" className="text-sm text-muted">Loading the selected workflow records…</p>}
    {data && <PostSelectionContent data={data} busy={busy} onPage={next => { request.current++; setData(null); setOffset(next) }} />}
  </DashboardCard>
}
