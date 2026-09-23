import { useEffect, useState } from 'react'
import { getCompany, getJobs } from '../../api/recruiter'
import { errorMessage } from '../../api/student'
import { useAuth } from '../../context/AuthContext'
import { Message, secondaryStyle } from '../../components/FormField'
import CompanyEditor from './CompanyEditor'
import DriveForm from './DriveForm'
import MatchPanel from './MatchPanel'

export default function TalentPage() {
  const { user } = useAuth()
  const [company, setCompany] = useState(null)
  const [jobs, setJobs] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    Promise.all([getCompany(), getJobs()]).then(([c, j]) => {
      if (active) { setCompany(c); setJobs(j); setSelected(j[0] || null) }
    }).catch(failure => { if (active) setError(errorMessage(failure)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [retry])
  function created(job) { setJobs([job, ...jobs]); setSelected(job) }
  return <div className="space-y-6">
    <header><p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">Explainability-first · Demo College {user.college_id}</p>
      <h1 className="mt-2 text-4xl font-bold text-navy">Talent Finder</h1>
      <p className="mt-3 max-w-2xl text-muted">A clear shortlist starts with a clear why. Set the role, inspect the evidence, and make the human decision.</p>
      <p className="mt-2 text-xs text-muted">Public hackathon prototype · synthetic demonstration only · self-reported profile inputs</p>
    </header>
    <Message error>{error}</Message>
    {error && <button onClick={() => setRetry(retry + 1)} className={secondaryStyle}>Retry loading</button>}
    {loading && <p role="status">Loading your company and drives…</p>}
    {company && <>
      <CompanyEditor company={company} onSaved={setCompany} />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <DriveForm onCreated={created} />
        <aside className="rounded-2xl border border-line bg-white p-6">
          <h2 className="text-xl font-bold text-navy">Your drives <span className="text-sm text-muted">({jobs.length})</span></h2>
          {jobs.length === 0 && <p className="mt-4 text-sm text-muted">Create your first drive to see matching results here. The seeded companies’ drives belong to their own recruiter accounts.</p>}
          <div className="mt-4 max-h-[32rem] space-y-3 overflow-y-auto">{jobs.map(job => <button key={job.id} type="button" aria-pressed={selected?.id === job.id}
            className={'w-full rounded-xl border p-4 text-left transition ' + (selected?.id === job.id ? 'border-saffron bg-warning-soft' : 'border-line hover:bg-paper')}
            onClick={() => setSelected(job)}><span className="block font-bold text-navy">{job.title}</span><span className="mt-1 block text-xs text-muted">₹{job.ctc} lakh/year · {job.eligible_branches.join(', ')}</span></button>)}</div>
        </aside>
      </div>
      {selected && <MatchPanel key={selected.id} job={selected} />}
      <details className="rounded-xl border border-line bg-white p-5"><summary className="cursor-pointer font-bold text-navy">Jugaad Dost 🤝 · Matching help</summary>
        <p className="mt-3 text-sm text-muted">This is a static help panel. Matching uses exact skill names, project keyword coverage, academics, existing assessment inputs and certificate count. Skills are compared with your role targets; scores are suggestions, not placement predictions. Review excluded profiles and record a human exception when justified.</p></details>
    </>}
  </div>
}
