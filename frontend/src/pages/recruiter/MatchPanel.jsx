import { useCallback, useEffect, useState } from 'react'
import { getMatches, runMatching } from '../../api/recruiter'
import { errorMessage } from '../../api/student'
import { FormField, buttonStyle, secondaryStyle, Message } from '../../components/FormField'
import CandidateCard from './CandidateCard'

export default function MatchPanel({ job }) {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('shortlisted')
  const [offset, setOffset] = useState(0)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    let active = true
    setLoading(true); setError(''); setData(null)
    getMatches(job.id, status, offset).then(result => { if (active) setData(result) })
      .catch(failure => { if (active) setError(errorMessage(failure)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [job.id, status, offset, revision])
  async function run() {
    setBusy(true); setError(''); setMessage('')
    try {
      await runMatching(job.id); setOffset(0); setRevision(v => v + 1)
      setMessage('Jugaad Ho Gaya ✓ Matching refreshed. Review the evidence before deciding.')
    } catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  const reviewed = useCallback(async () => {
    setOffset(0); setRevision(v => v + 1); setMessage('Manual decision recorded with its reason and scoring evidence.')
  }, [])
  const total = data ? (status === 'all' ? data.total : data[status]) : 0
  return <section className="mt-8 space-y-5">
    <div className="rounded-2xl bg-navy p-6 text-white">
      <p className="text-xs font-bold uppercase tracking-wider text-saffron">02 · Explainable matching</p>
      <h2 className="mt-2 text-2xl font-bold">{job.title}</h2>
      <p className="mt-2 text-sm text-white/80">₹{job.ctc} lakh/year · CGPA ≥ {job.min_cgpa} · Backlogs ≤ {job.max_backlogs} · {job.eligible_branches.join(', ')}</p>
      <p className="mt-2 text-sm text-white/80">Skill targets: {job.required_skills.map(s => s.skill_name + ' ' + s.min_proficiency + '/100').join(' · ')}</p>
      <p className="mt-2 text-sm text-white/80">Shortlist threshold: {job.min_match_score}/100. Eligibility rules apply before shortlist ranking.</p>
      <button onClick={run} disabled={busy || loading} className={buttonStyle + ' mt-5'}>{busy ? 'Matching profiles…' : 'Run AI Matching'}</button>
      <p className="mt-3 text-xs text-white/80">This button runs keyword matching and a weighted rule, with no trained model. Starting weights are unvalidated assumptions. Manual decisions survive reruns.</p>
    </div>
    <Message error>{error}</Message><Message>{message}</Message>
    {data && <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{[['Profiles reviewed',data.total],['Shortlisted for review',data.shortlisted],['Excluded',data.excluded],['Manual decisions',data.overridden]].map(([label,count]) =>
      <div key={label} className="rounded-xl border border-line bg-white p-4"><p className="text-2xl font-bold text-navy">{count}</p><p className="text-xs text-muted">{label}</p></div>)}</div>}
    <div className="flex flex-wrap items-end justify-between gap-4">
      <FormField label="Candidate view" value={status} disabled={busy} onChange={e => { setStatus(e.target.value); setOffset(0) }}>
        <option value="shortlisted">Shortlisted for review</option><option value="excluded">Excluded / manually rejected</option><option value="all">All candidates</option>
      </FormField>
      <p className="text-xs text-muted">Descending score · ties by student ID · recommendations for human review</p>
    </div>
    {loading && <p role="status">Loading explained results…</p>}
    {!loading && data?.candidates.length === 0 && <div className="rounded-xl border border-dashed border-line bg-white p-6 text-muted">
      {data.total === 0 ? 'No matching run yet. Run matching to review this college’s profiles.' : 'No candidates in this view. Review excluded candidates or adjust the view.'}</div>}
    {data?.candidates.map((candidate, index) => <CandidateCard key={candidate.id + ':' + candidate.calculated_at + ':' + candidate.audit.length}
      candidate={candidate} position={offset + index + 1} onReviewed={reviewed} />)}
    {data && total > 0 && <div className="flex items-center justify-between gap-3">
      <button className={secondaryStyle} disabled={offset === 0 || loading || busy} onClick={() => setOffset(Math.max(0, offset - 5))}>Previous</button>
      <p className="text-sm text-muted">{offset + 1}–{Math.min(offset + 5, total)} of {total}</p>
      <button className={secondaryStyle} disabled={offset + 5 >= total || loading || busy} onClick={() => setOffset(offset + 5)}>Next</button>
    </div>}
  </section>
}
