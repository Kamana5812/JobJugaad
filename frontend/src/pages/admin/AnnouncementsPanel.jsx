import { useCallback, useEffect, useRef, useState } from 'react'
import { getAnnouncementOptions, announcementErrorMessage } from '../../api/announcements'
import DashboardCard from '../../components/DashboardCard'
import { Message, secondaryStyle } from '../../components/FormField'
import AnnouncementCompose from './AnnouncementCompose'
import AnnouncementHistory from './AnnouncementHistory'

export default function AnnouncementsPanel() {
  const [options, setOptions] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [revision, setRevision] = useState(0)
  const [draftLocked, setDraftLocked] = useState(false)
  const request = useRef(0)
  const refresh = useCallback(async () => {
    const ticket = ++request.current; setBusy(true); setError('')
    try { const result = await getAnnouncementOptions(); if (ticket === request.current) setOptions(result) }
    catch (failure) { if (ticket === request.current) setError(announcementErrorMessage(failure)) }
    finally { if (ticket === request.current) setBusy(false) }
  }, [])
  useEffect(() => { refresh(); return () => { request.current++ } }, [refresh])
  return <section className="space-y-5">
    <header><h2 className="text-xl font-semibold text-navy">Drive announcements</h2><p className="mt-2 text-sm text-muted">Publish targeted updates and manual reminders to students in this college. Preview the current audience before confirming. Messages appear in the in-app feed only.</p></header>
    <DashboardCard title="Compose a drive announcement" label="Draft → audience preview → administrator publication">
      <button className={secondaryStyle + ' mb-4'} disabled={busy || draftLocked} onClick={refresh}>{busy ? 'Loading choices…' : 'Refresh drive and branch choices'}</button><Message error>{error}</Message>
      {options && <><p className="mb-4 text-sm text-muted">{options.explanation}</p>{options.jobs.length ? <AnnouncementCompose options={options} onLockChange={setDraftLocked} onPublished={() => setRevision(value => value + 1)} /> : <p className="text-sm text-muted">No drive choices are currently available. An approved recruiter must create a drive before an officer can publish its updates.</p>}</>}
    </DashboardCard>
    <AnnouncementHistory key={revision} />
  </section>
}
