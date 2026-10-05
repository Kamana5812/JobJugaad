import { useState } from 'react'
import { getApplicationProfile } from '../api/driveWorkflow'
import { errorMessage } from '../api/student'
import { Message, secondaryStyle } from './FormField'
import ReadinessCard from './ReadinessCard'

export default function ApplicationProfile({ jobId, application, admin, onExpired }) {
  const [profile, setProfile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  if (!['submitted', 'under_review', 'shortlisted'].includes(application.status)) return null
  async function load() {
    setBusy(true); setError(''); setProfile(null)
    try { setProfile(await getApplicationProfile(admin, jobId, application.id)) }
    catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <div className="space-y-4 border-t border-line pt-4">
    <button type="button" className={secondaryStyle} disabled={busy} onClick={profile ? () => setProfile(null) : load}>{busy ? 'Loading…' : profile ? 'Close current profile' : 'Review current profile'}</button>
    <Message error>{error}</Message>
    {profile && <div className="space-y-4"><p className="text-xs text-muted">Current self-reported profile, shared through this active application. The submission’s frozen evidence remains unchanged.</p>
      <p className="font-bold text-navy">{profile.name} · {profile.branch} · CGPA {profile.cgpa ?? 'not recorded'}</p>
      <ReadinessCard readiness={profile.readiness} />
      <p className="text-sm text-navy">Skills: {profile.skills.map(s => `${s.skill_name} (${s.proficiency}/100)`).join(', ') || 'None recorded'}</p>
      {['projects', 'certifications'].map(kind => <section key={kind}><h4 className="font-bold capitalize text-navy">{kind}</h4>{profile[kind].map((item, i) => <p className="mt-2 whitespace-pre-wrap text-sm" key={i}><strong>{item.title}</strong> — {item.description}</p>)}</section>)}
      <section><h4 className="font-bold text-navy">Experience</h4>{profile.experiences.map((item, i) => <p key={i} className="mt-2 whitespace-pre-wrap text-sm"><strong>{item.role} · {item.organization}</strong> ({item.kind})<br />{item.description}<br />{item.reference}</p>)}</section>
      <details><summary className="cursor-pointer font-bold text-navy">Extracted resume text</summary><p className="mt-2 whitespace-pre-wrap text-sm">{profile.resume_text || 'No resume text recorded.'}</p></details>
    </div>}
  </div>
}
