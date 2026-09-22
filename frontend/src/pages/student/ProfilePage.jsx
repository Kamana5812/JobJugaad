import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getProfile, saveProfile, errorMessage } from '../../api/student'
import { FormField, buttonStyle, secondaryStyle, Message } from '../../components/FormField'
import ReadinessCard from '../../components/ReadinessCard'
import EvidenceEditor from '../../components/EvidenceEditor'
import ResumeUpload from '../../components/ResumeUpload'

const nullable = (value) => value === '' || value === null ? null : Number(value)
function editable(profile) {
  const { name, branch, cgpa, backlog_count, aptitude_score, communication_score, interview_score, skills, projects, certifications } = profile
  return { name, branch, cgpa: cgpa ?? '', backlog_count, aptitude_score: aptitude_score ?? '',
    communication_score: communication_score ?? '', interview_score: interview_score ?? '', skills, projects, certifications }
}
export default function ProfilePage() {
  const { user, logout } = useAuth()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState(null)
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  async function load() {
    setLoading(true); setError('')
    try { const value = await getProfile(user.student_id); setProfile(value); setForm(editable(value)); setDirty(false) }
    catch (failure) { if (failure.response?.status === 401) logout(); else setError(errorMessage(failure)) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [user.student_id])
  useEffect(() => {
    if (!dirty) return
    const warn = (event) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])
  function change(key, value) { setForm((current) => ({ ...current, [key]: value })); setDirty(true); setNotice('') }
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      const payload = { ...form, cgpa: nullable(form.cgpa), backlog_count: Number(form.backlog_count),
        aptitude_score: nullable(form.aptitude_score), communication_score: nullable(form.communication_score),
        interview_score: nullable(form.interview_score),
        skills: form.skills.map((skill) => ({ ...skill, proficiency: Number(skill.proficiency) })) }
      const saved = await saveProfile(profile.id, payload)
      setProfile(saved); setForm(editable(saved)); setDirty(false)
      setNotice('Jugaad Ho Gaya ✓ Profile saved and readiness recalculated.')
    } catch (failure) { if (failure.response?.status === 401) logout(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  if (loading) return <p role="status" className="rounded-2xl border border-line bg-white p-8 text-navy">Loading your saved profile… The demo server may need a moment to wake up.</p>
  if (!profile) return <div className="space-y-4"><Message error>{error}</Message><button onClick={load} className={buttonStyle}>Retry profile</button></div>
  return <div className="space-y-8">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-xs font-bold uppercase tracking-widest text-muted">Student portal · Demo College {profile.college_id}</p>
        <h1 className="mt-2 text-3xl font-bold text-navy">Your career, with a clear why.</h1><p className="mt-2 text-muted">Hello, {profile.name}. Start with what you know, then build from here.</p></div>
      <a href="#profile-editor" className={secondaryStyle}>Edit my profile ↓</a>
    </div>
    <ReadinessCard readiness={profile.readiness} dirty={dirty} />
    <ResumeUpload profile={profile} disabled={busy} onBusyChange={setUploading} onExpired={logout} onUploaded={(value) => setProfile(value)} />
    <section id="profile-editor" aria-labelledby="profile-title" className="rounded-3xl border border-line bg-white p-6 sm:p-8">
      <h2 id="profile-title" className="text-xl font-bold text-navy"><span className="mr-3 text-saffron">03</span>Build your profile evidence.</h2>
      <p className="mt-2 text-sm leading-6 text-muted">Keep it accurate. Leave unknown assessments blank; missing information contributes zero, not a judgment of ability.</p>
      <form onSubmit={save} className="mt-6 space-y-6">
        <fieldset disabled={busy || uploading} className="space-y-6">
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <FormField label="Full name" required maxLength="100" value={form.name} onChange={(e) => change('name', e.target.value)} />
            <FormField label="Branch" required maxLength="80" value={form.branch} onChange={(e) => change('branch', e.target.value)} />
            <FormField label="CGPA / 10" type="number" min="0" max="10" step="0.01" value={form.cgpa} onChange={(e) => change('cgpa', e.target.value)} />
            <FormField label="Active backlogs" type="number" min="0" max="100" step="1" required value={form.backlog_count} onChange={(e) => change('backlog_count', e.target.value)} />
          </div>
          <div className="rounded-2xl bg-paper p-5">
            <h3 className="font-bold text-navy">Existing assessment results</h3>
            <p className="mt-1 text-xs leading-5 text-muted">Self-reported scores from assessments taken elsewhere. JobJugaad does not conduct interviews or assessments.</p>
            <div className="mt-4 grid gap-5 sm:grid-cols-3">{[['aptitude_score','Aptitude / 100'],['communication_score','Communication / 100'],['interview_score','Interview / 100']].map(([key, label]) =>
              <FormField key={key} label={label} type="number" min="0" max="100" step="0.1" value={form[key]} onChange={(e) => change(key, e.target.value)} />)}</div>
          </div>
          <EvidenceEditor title="Technical skills" kind="skills" items={form.skills} onChange={(value) => change('skills', value)} limit={30} />
          <EvidenceEditor title="Projects" kind="projects" items={form.projects} onChange={(value) => change('projects', value)} limit={20} />
          <EvidenceEditor title="Certifications" kind="certifications" items={form.certifications} onChange={(value) => change('certifications', value)} limit={20} />
          <p className="text-xs leading-5 text-muted">Certifications and backlogs are saved for your profile but do not change this six-factor readiness formula. Project count is a simple proxy; project quality is not assessed.</p>
        </fieldset>
        <Message error>{error}</Message><Message>{notice}</Message>
        <div className="flex flex-wrap items-center gap-4"><button className={buttonStyle} disabled={busy || uploading || !dirty}>{busy ? 'Saving…' : 'Save profile & recalculate'}</button>
          <span className="text-sm text-muted">{dirty ? 'You have unsaved changes.' : 'Your profile is up to date.'}</span></div>
      </form>
    </section>
    <aside className="rounded-2xl bg-navy p-6 text-white"><h2 className="font-bold">Jugaad Dost 🤝</h2>
      <p className="mt-1 text-xs text-white/70">Quick help · static FAQ</p>
      <details className="mt-4"><summary className="cursor-pointer text-sm font-semibold">Why did uploading my resume not change my score?</summary><p className="mt-2 text-sm leading-6 text-white/80">Uploading stores readable text for your review. Add skills, projects, academics, and existing assessment scores to your profile, then save to recalculate.</p></details>
      <details className="mt-4"><summary className="cursor-pointer text-sm font-semibold">Is this a placement prediction?</summary><p className="mt-2 text-sm leading-6 text-white/80">No. It is a proposed weighted rule based on self-reported evidence. It has not been validated against real placement outcomes. A person should review the evidence before making any decision.</p></details>
    </aside>
  </div>
}
