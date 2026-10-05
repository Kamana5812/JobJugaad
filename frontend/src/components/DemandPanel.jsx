import { useEffect, useState } from 'react'
import { getRecordedDemand } from '../api/driveWorkflow'
import { errorMessage } from '../api/student'
import { Message, secondaryStyle } from './FormField'

export default function DemandPanel({ admin = false }) {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function load() {
    setBusy(true); setError('')
    try { setData(await getRecordedDemand(admin)) }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [admin])
  return <section id="hiring-demand" className="space-y-4 rounded-xl border border-line bg-white p-6">
    <div className="flex flex-wrap justify-between gap-3"><h2 className="text-xl font-bold text-navy">Recorded hiring demand</h2><button className={secondaryStyle} disabled={busy} onClick={load}>{busy ? 'Loading…' : 'Refresh demand'}</button></div>
    <Message error>{error}</Message>
    {data && <><p className="text-sm text-muted">{data.scope} · {data.open_drives} open / {data.total_drives} total drives</p><p className="text-sm leading-6 text-muted">{data.explanation}</p>
      <h3 className="font-bold text-navy">Reviewed skills in open drives</h3><div className="flex flex-wrap gap-2">{data.skills.map(skill => <span key={skill.skill_name} className="rounded-lg bg-paper p-3 text-sm">{skill.skill_name} · {skill.open_drive_count} drive(s)</span>)}</div>
      {!data.drives.length && <p className="text-sm text-muted">No recorded drives yet.</p>}
      {data.drives.length > 0 && <div className="overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Distinct student-drive counts by recorded milestone</caption><thead><tr>{['Drive', 'Submitted', 'Active', 'Shortlisted', 'Selected', 'Accepted', 'Joined'].map(label => <th key={label} className="p-3 text-navy" scope="col">{label}</th>)}</tr></thead><tbody>{data.drives.map(drive => <tr key={drive.job_id} className="border-t border-line"><th scope="row" className="p-3 font-medium">{drive.title} · {drive.is_open ? 'Open' : 'Closed'}</th>{['submitted', 'active_applications', 'shortlisted', 'selected', 'accepted', 'joined'].map(key => <td key={key} className="p-3">{drive[key]}</td>)}</tr>)}</tbody></table></div>}
    </>}
  </section>
}
