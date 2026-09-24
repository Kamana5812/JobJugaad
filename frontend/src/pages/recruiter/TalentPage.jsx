import { useEffect, useState } from 'react'
import { getCompany, getJobs } from '../../api/recruiter'
import { errorMessage } from '../../api/student'
import { useAuth } from '../../context/AuthContext'
import { Message, buttonStyle, secondaryStyle } from '../../components/FormField'
import PortalHero, { PortalSections } from '../../components/PortalHero'
import Pagination from '../../components/Pagination'
import CompanyEditor from './CompanyEditor'
import DriveForm from './DriveForm'
import MatchPanel from './MatchPanel'

export default function TalentPage() {
  const { user, logout } = useAuth()
  const [company, setCompany] = useState(null)
  const [jobs, setJobs] = useState([])
  const [selected, setSelected] = useState(null)
  const [offset, setOffset] = useState(0)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    Promise.all([getCompany(), getJobs()]).then(([c, j]) => {
      if (active) { setCompany(c); setJobs(j); setSelected(j[0] || null); setOffset(0) }
    }).catch(failure => { if (active) { if (failure.response?.status === 401) logout(); else setError(errorMessage(failure)) } })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [retry])
  function created(job) { setJobs([job, ...jobs]); setSelected(job); setOffset(0); setNotice(`Drive “${job.title}” created. Its matching view is ready above.`) }
  return <div className="space-y-8">
    <PortalHero role="recruiter" collegeId={user.college_id} description="A clear shortlist starts with a clear why. Define the role, inspect the evidence, and make the human decision.">
      <a href="#create-drive" className={buttonStyle}>Create a drive →</a><a href="#matching" className={secondaryStyle}>Review matches ↓</a>
    </PortalHero>
    <PortalSections label="Talent Finder sections" items={[["drives", "Your drives"], ["matching", "Matching & candidates"], ["create-drive", "Create a drive"], ["company", "Company profile"]]} />
    <Message error>{error}</Message>{error && <button onClick={() => setRetry(retry + 1)} className={secondaryStyle}>Retry loading</button>}
    {loading && <p role="status">Loading your company and drives…</p>}
    {company && <>
      <section id="drives" className="scroll-mt-6 rounded-3xl border border-line bg-white p-6 sm:p-8">
        <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-widest text-muted">{company.name}</p><h2 className="mt-2 text-2xl font-bold text-navy"><span className="mr-3 text-saffron-deep">01</span>Your drives</h2></div><p className="text-sm text-muted">{jobs.length} recorded drive{jobs.length === 1 ? '' : 's'}</p></div>
        <p className="mt-3 text-sm text-muted">Choose a drive to review its requirements and explained candidate matches below.</p>
        {jobs.length === 0 && <div className="mt-5 rounded-2xl border border-dashed border-line bg-paper p-6"><p className="text-sm text-muted">Your company has no drives yet. Seeded drives belong to their own recruiter accounts.</p><a href="#create-drive" className={buttonStyle + ' mt-4'}>Create your first drive →</a></div>}
        <div className="my-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{jobs.slice(offset, offset + 6).map(job => <button key={job.id} type="button" aria-pressed={selected?.id === job.id} onClick={() => setSelected(job)}
          className={'rounded-2xl border p-5 text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy ' + (selected?.id === job.id ? 'border-saffron bg-warning-soft' : 'border-line bg-paper hover:border-navy/30')}>
          <span className="block text-[11px] font-bold uppercase tracking-widest text-muted">{selected?.id === job.id ? '✓ Selected drive' : 'Drive #' + job.id}</span><span className="mt-3 block text-lg font-bold text-navy">{job.title}</span><span className="mt-3 block text-sm text-muted">₹{job.ctc} LPA · CGPA ≥ {job.min_cgpa}</span><span className="mt-2 block text-xs leading-5 text-muted">{job.eligible_branches.join(', ')}</span></button>)}</div>
        {jobs.length > 6 && <Pagination data={{ total: jobs.length, offset, limit: 6 }} busy={loading} onPage={setOffset} />}
      </section>
      <div id="matching" className="scroll-mt-6">{selected ? <MatchPanel key={selected.id} job={selected} /> : <p className="rounded-2xl border border-line bg-white p-6 text-sm text-muted">Create a drive to run keyword matching and review candidates.</p>}</div>
      <div id="create-drive" className="scroll-mt-6 space-y-4"><DriveForm onCreated={created} /><Message>{notice}</Message>{notice && <a href="#matching" className={buttonStyle}>Review the new drive’s matches ↑</a>}</div>
      <div id="company" className="scroll-mt-6"><CompanyEditor company={company} onSaved={setCompany} /></div>
      <details className="rounded-2xl border border-line bg-white p-6"><summary className="cursor-pointer font-bold text-navy">Jugaad Dost 🤝 · Matching help</summary><p className="mt-3 text-sm leading-7 text-muted">This is a static help panel. Matching uses exact skill names, project keyword coverage, academics, existing assessment inputs and certificate count. Scores are suggestions, not placement predictions. Review excluded profiles and record a human exception when justified.</p></details>
    </>}
  </div>
}
