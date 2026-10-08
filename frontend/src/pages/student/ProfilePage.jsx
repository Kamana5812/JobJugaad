import { lazy, Suspense, useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getProfile, saveProfile, errorMessage, askJugaadDost } from '../../api/student'
import { FormField, buttonStyle, secondaryStyle, Message } from '../../components/FormField'
import BTechModelPanel from './BTechModelPanel'
import PlacementModelPanel from './PlacementModelPanel'
import ReadinessCard from '../../components/ReadinessCard'
import EvidenceEditor from '../../components/EvidenceEditor'
import ResumeUpload from '../../components/ResumeUpload'
import ResumeSuggestions from '../../components/ResumeSuggestions'
import PortalHero, { PortalSections } from '../../components/PortalHero'
import OpportunitiesPanel from './OpportunitiesPanel'
import InterviewsPanel from './InterviewsPanel'
import ApplicationsPanel from './ApplicationsPanel'
import AssessmentPanel from './AssessmentPanel'
import ExperienceEditor from '../../components/ExperienceEditor'

const MarketRolesPanel = lazy(() => import('./MarketRolesPanel'))

const nullable = (value) => value === '' || value === null ? null : Number(value)
function editable(profile) {
  const { name, branch, cgpa, backlog_count, aptitude_score, communication_score, interview_score, skills, projects, certifications } = profile
  return { name, branch, cgpa: cgpa ?? '', backlog_count, aptitude_score: aptitude_score ?? '',
    communication_score: communication_score ?? '', interview_score: interview_score ?? '', skills, projects, certifications, experiences: profile.experiences ?? [] }
}
export default function ProfilePage() {
  const { user, logout } = useAuth()
  const [profile, setProfile] = useState(null)
  const [revision, setRevision] = useState(0)
  const [form, setForm] = useState(null)
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([{ role: 'dost', content: 'Namaste! I am Jugaad Dost, your placement copilot. Ask me about your eligibility or readiness!' }])
  const [chatLoading, setChatLoading] = useState(false)
  async function load() {
    setLoading(true); setError('')
    try { const value = await getProfile(user.student_id); setProfile(value); setForm(editable(value)); setDirty(false) }
    catch (failure) { if (failure.response?.status === 401) logout(true); else setError(errorMessage(failure)) }
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
  function suggested(items) {
    setForm(current => {
      const next = { ...current, skills: [...current.skills], projects: [...current.projects], certifications: [...current.certifications] }
      for (const item of items) {
        if (['name', 'branch', 'cgpa'].includes(item.field)) next[item.field] = item.value
        if (item.field === 'skill' && next.skills.length < 30 && !next.skills.some(s => s.skill_name.toLowerCase() === item.value)) next.skills.push({ skill_name: item.value, proficiency: item.proficiency })
        const key = item.field === 'project' ? 'projects' : item.field === 'certification' ? 'certifications' : null
        if (key && next[key].length < 20 && !next[key].some(e => e.title === item.value)) next[key].push({ title: item.value, description: item.detail || item.source })
      }
      return next
    }); setDirty(true); setNotice('Resume suggestions are in your unsaved editor. Review every field before saving; duplicates and collection limits are preserved.')
  }
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      const payload = { ...form, cgpa: nullable(form.cgpa), backlog_count: Number(form.backlog_count),
        aptitude_score: nullable(form.aptitude_score), communication_score: nullable(form.communication_score),
        interview_score: nullable(form.interview_score),
        skills: form.skills.map((skill) => ({ ...skill, proficiency: Number(skill.proficiency) })) }
      const saved = await saveProfile(profile.id, payload)
      setProfile(saved); setForm(editable(saved)); setDirty(false); setRevision(value => value + 1)
      setNotice('Jugaad Ho Gaya ✓ Profile saved and readiness recalculated.')
    } catch (failure) { if (failure.response?.status === 401) logout(true); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  if (loading) return <p role="status" className="rounded-2xl border border-line bg-white p-8 text-navy">Loading your saved profile… The service may need a moment to wake up.</p>
  if (!profile) return <div className="space-y-4"><Message error>{error}</Message><button onClick={load} className={buttonStyle}>Retry profile</button></div>
  return <div className="space-y-8">
    <PortalHero role="student" collegeId={profile.college_id} description={`Hello, ${profile.name}. Understand where you stand, find the gaps, and plan your next step.`}>
      <a href="#profile-editor" className={buttonStyle}>Update my profile →</a><a href="#opportunities" className={secondaryStyle}>Explore opportunities ↓</a>
    </PortalHero>
    <PortalSections label="Career Copilot sections" items={[["readiness", "Readiness"], ["skill-gaps", "Skill gaps"], ["opportunities", "College drives"], ["applications", "My applications"], ["interviews", "My interviews"], ["market-roles", "Market roles"], ["resume", "Resume"], ["profile-editor", "My profile"], ["placement-models", "Placement models"]]} />
    <section aria-label="Saved profile summary" className="flex flex-wrap items-center justify-between gap-6 rounded-2xl border border-line bg-white p-6">
      <div><p className="text-xs font-bold uppercase tracking-widest text-muted">Your saved profile</p><h2 className="mt-2 text-xl font-bold text-navy">{profile.name}</h2><p className="mt-1 text-sm text-muted">{profile.branch} · {profile.cgpa === null ? 'CGPA not recorded' : `CGPA ${profile.cgpa}/10`} · Student #{profile.id}</p></div>
      <dl className="flex flex-wrap gap-8">{[['Skills', profile.skills.length], ['Projects', profile.projects.length], ['Certifications', profile.certifications.length]].map(([label, count]) => <div key={label}><dt className="text-xs text-muted">{label}</dt><dd className="mt-1 text-2xl font-bold text-navy">{count}</dd></div>)}</dl>
    </section>
    <div id="readiness" className="scroll-mt-6"><ReadinessCard readiness={profile.readiness} dirty={dirty} /></div>
    <AssessmentPanel studentId={profile.id} />
    <OpportunitiesPanel key={revision} studentId={profile.id} revision={revision} dirty={dirty} onExpired={logout} />
    <ApplicationsPanel studentId={profile.id} dirty={dirty} onExpired={logout} />
    <InterviewsPanel studentId={profile.id} />
    <Suspense fallback={<p role="status">Loading historical market references…</p>}><MarketRolesPanel /></Suspense>
    <div id="resume" className="scroll-mt-6"><ResumeUpload sectionNumber="04" profile={profile} disabled={busy} onBusyChange={setUploading} onExpired={logout} onUploaded={(value) => setProfile(value)} /></div>
    <ResumeSuggestions profile={profile} disabled={busy || uploading} onSuggested={suggested} onExpired={logout} />
    <section id="profile-editor" aria-labelledby="profile-title" className="scroll-mt-6 rounded-xl border border-line bg-white p-6 sm:p-8">
      <h2 id="profile-title" className="text-xl font-bold text-navy"><span className="mr-3 text-saffron-deep">05</span>Build your profile evidence.</h2>
      <p className="mt-2 text-sm leading-6 text-muted">Keep it accurate. Staff-adopted results take precedence in scoring and are named in the breakdown; your self-reports stay editable. Leave unknown assessments blank; missing information contributes zero, not a judgment of ability.</p>
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
          <ExperienceEditor items={form.experiences} onChange={value => change('experiences', value)} />
          <p className="text-xs leading-5 text-muted">Certifications and backlogs are saved for your profile but do not change this six-factor readiness formula. Project count is a simple proxy; project quality is not assessed.</p>
        </fieldset>
        <Message error>{error}</Message><Message>{notice}</Message>
        <div className="flex flex-wrap items-center gap-4"><button className={buttonStyle} disabled={busy || uploading || !dirty}>{busy ? 'Saving…' : 'Save profile & recalculate'}</button>
          <span className="text-sm text-muted">{dirty ? 'You have unsaved changes.' : 'Your profile is up to date.'}</span></div>
      </form>
    </section>
    <div id="placement-models" className="scroll-mt-6 space-y-8"><BTechModelPanel sectionNumber="06" studentId={profile.id} onExpired={logout} />
    <PlacementModelPanel sectionNumber="07" studentId={profile.id} onExpired={logout} /></div>
    <aside className="rounded-2xl bg-navy p-6 text-white flex flex-col h-96">
      <h2 className="font-bold">Jugaad Dost 🤝</h2>
      <p className="mt-1 text-xs text-white/70 mb-4">Your AI Placement Copilot</p>
      
      <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
        {chatMessages.map((msg, i) => (
          <div key={i} className={`p-3 rounded-xl text-sm ${msg.role === 'user' ? 'bg-white/10 ml-8' : 'bg-blue-600/50 mr-8'} whitespace-pre-wrap`}>
            {msg.content}
          </div>
        ))}
        {chatLoading && (
          <div className="p-3 rounded-xl text-sm bg-blue-600/50 mr-8 animate-pulse">
            Dost is thinking...
          </div>
        )}
      </div>

      <form 
        className="flex gap-2"
        onSubmit={async (e) => {
          e.preventDefault()
          if (!chatInput.trim() || chatLoading) return
          
          const userMsg = chatInput.trim()
          setChatInput('')
          setChatMessages(prev => [...prev, { role: 'user', content: userMsg }])
          setChatLoading(true)
          
          try {
            const res = await askJugaadDost(profile.id, userMsg)
            setChatMessages(prev => [...prev, { role: 'dost', content: res.reply }])
          } catch (err) {
            setChatMessages(prev => [...prev, { role: 'dost', content: 'Oops! I am having trouble connecting right now.' }])
          } finally {
            setChatLoading(false)
          }
        }}
      >
        <input 
          type="text" 
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          placeholder="Ask about your eligibility or readiness..." 
          className="flex-1 bg-white/10 rounded-lg px-4 py-2 text-sm text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500 border-none"
        />
        <button 
          type="submit" 
          disabled={chatLoading}
          className="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded-lg text-sm font-bold transition-colors disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </aside>
  </div>
}
