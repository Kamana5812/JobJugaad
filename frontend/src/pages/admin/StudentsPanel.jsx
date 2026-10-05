import { useEffect, useState } from 'react'
import { getCollegeStudents, getCollegeStudentProfile } from '../../api/admin'
import { errorMessage } from '../../api/student'
import { FormField, Message, secondaryStyle } from '../../components/FormField'
import Pagination from '../../components/Pagination'
import ReadinessCard from '../../components/ReadinessCard'

export default function StudentsPanel() {
  const [query, setQuery] = useState('')
  const [applied, setApplied] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState(null)
  const [profile, setProfile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function load() {
    setBusy(true); setError(''); setProfile(null)
    try { setData(await getCollegeStudents({ query: applied, offset, limit: 20 })) }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  async function review(id) {
    setBusy(true); setError(''); setProfile(null)
    try { setProfile(await getCollegeStudentProfile(id)) }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [applied, offset])
  return <section className="space-y-5 rounded-xl border border-line bg-white p-6">
    <h2 className="text-xl font-bold text-navy">College student directory</h2>
    <p className="text-sm text-muted">Review your college’s recorded profiles for admission and mentoring. Profile edits belong to the student; reviewed assessment evidence is recorded separately. Recruiters need an active application to review a current profile.</p>
    <form className="flex flex-wrap items-end gap-3" onSubmit={event => { event.preventDefault(); setOffset(0); setApplied(query) }}><FormField label="Find by name or email" maxLength={100} value={query} onChange={e => setQuery(e.target.value)} /><button className={secondaryStyle} disabled={busy}>Search students</button><button type="button" className={secondaryStyle} disabled={busy} onClick={load}>Refresh</button></form>
    <Message error>{error}</Message>{busy && <p role="status">Loading…</p>}
    {data?.items.map(student => <div key={student.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line p-4"><div><h3 className="font-bold text-navy">{student.name} · #{student.id}</h3><p className="text-sm text-muted">{student.branch} · {student.email}{student.restricted ? ' · Restricted account' : ''}</p></div><button className={secondaryStyle} disabled={busy} onClick={() => review(student.id)}>Review profile #{student.id}</button></div>)}
    {data?.total === 0 && <p className="text-muted">No students match this search in your college.</p>}
    <Pagination data={data} busy={busy} onPage={setOffset} />
    {profile && <section className="space-y-4 rounded-xl bg-paper p-5"><h3 className="text-lg font-bold text-navy">Current profile · {profile.name}</h3><ReadinessCard readiness={profile.readiness} />
      <p className="text-sm">Recorded skills: {profile.skills.map(s => `${s.skill_name} ${s.proficiency}/100`).join(', ') || 'None'}</p>
      {['projects', 'certifications'].map(kind => <div key={kind}><h4 className="font-bold capitalize">{kind}</h4>{profile[kind].map((item, i) => <p key={i} className="mt-2 whitespace-pre-wrap text-sm"><strong>{item.title}</strong> — {item.description}</p>)}</div>)}
      <h4 className="font-bold">Experience</h4>{profile.experiences.map((item, i) => <p key={i} className="whitespace-pre-wrap text-sm"><strong>{item.role} · {item.organization}</strong><br />{item.description}</p>)}
      <details><summary className="cursor-pointer font-bold">Extracted resume text</summary><p className="mt-3 whitespace-pre-wrap text-sm">{profile.resume_text || 'No resume text recorded.'}</p></details>
      <button className={secondaryStyle} onClick={() => setProfile(null)}>Close profile review</button>
    </section>}
  </section>
}
