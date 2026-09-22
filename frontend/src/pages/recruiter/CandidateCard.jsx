import { useState } from 'react'
import FactorTable from '../../components/FactorTable'
import { FormField, secondaryStyle, Message } from '../../components/FormField'
import { overrideMatch } from '../../api/recruiter'
import { errorMessage } from '../../api/student'

export default function CandidateCard({ candidate: c, position, onReviewed }) {
  const [reason, setReason] = useState('')
  const [action, setAction] = useState('promote')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function review(event) {
    event.preventDefault(); setBusy(true); setError('')
    try { await overrideMatch(c.job_id, c.id, { action, reason }); setReason(''); await onReviewed() }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <article className="rounded-2xl border border-line bg-white p-5 shadow-sm sm:p-6" aria-label={c.student_name}>
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="text-xs font-bold uppercase tracking-wider text-muted">Position {position} · {c.branch} · Student #{c.student_id}</p>
        <h3 className="mt-1 text-xl font-bold text-navy">{c.student_name}</h3>
        <p className="mt-2 inline-block rounded-full bg-paper px-3 py-1 text-xs font-bold text-navy">{c.shortlist_status === 'shortlisted' ? '✓ Shortlisted for review' : '⚠ Excluded from shortlist'}{c.override_action && ' · Manual ' + c.override_action}</p>
      </div>
      <div className="text-right"><p className="text-3xl font-bold text-navy">{c.match_score}<span className="text-sm text-muted"> /100</span></p><p className="text-xs text-muted">Weighted match score</p></div>
    </div>
    {c.override_action && <p className="mt-4 rounded-xl bg-[#FDF0E3] p-3 text-sm text-navy">A recruiter manually {c.override_action === 'promote' ? 'promoted' : 'rejected'} this candidate. The calculated recommendation below is retained for review.</p>}
    <p className="my-4 text-sm leading-6">{c.explanation}</p>
    <FactorTable factors={c.factor_breakdown} />
    {c.missing_requirements.length > 0 && <div className="mt-4 rounded-xl bg-[#FDF0E3] p-4">
      <h4 className="font-bold text-navy">Requirements and review flags</h4><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{c.missing_requirements.map((item, i) => <li key={i}>{item}</li>)}</ul>
    </div>}
    <details className="mt-4 rounded-xl border border-line p-4">
      <summary className="cursor-pointer font-bold text-navy">Kahan Kami Hai? · Skill-by-skill comparison</summary>
      <div className="mt-3 space-y-3">{[...c.skill_gaps].sort((a,b) => ({critical:0,gap:1,'on-track':2}[a.status] - {critical:0,gap:1,'on-track':2}[b.status])).map(g =>
        <div key={g.skill_name} className="border-t border-line pt-3"><p className="flex flex-wrap items-center justify-between gap-2 font-semibold text-navy">{g.skill_name}
          <span className={'rounded-full px-3 py-1 text-xs ' + (g.status === 'on-track' ? 'bg-[#E2F3E9] text-navy' : g.status === 'critical' ? 'bg-[#FBE6E6] text-[#922B2B]' : 'bg-[#FDF0E3] text-navy')}>{g.status}</span></p>
          <p className="mt-2 text-sm">{g.explanation}</p><p className="mt-1 text-xs text-muted">Shortfall: {g.shortfall} points. {g.next_step}</p></div>)}</div>
    </details>
    <p className="mt-4 text-sm"><strong className="text-navy">Your Next Jugaad: </strong>{c.next_step}</p>
    <p className="mt-3 text-xs leading-5 text-muted">{c.methodology}</p>
    <p className="mt-2 text-xs text-muted">Calculated {new Date(c.calculated_at).toLocaleString()}. Rerun matching after profile changes.</p>
    <details className="mt-4 border-t border-line pt-4">
      <summary className="cursor-pointer text-sm font-bold text-navy">Human review · promote or reject</summary>
      <p className="my-3 text-xs text-muted">Override the shortlist regardless of score. The reason, reviewer, time and original scoring evidence are recorded.</p>
      <form onSubmit={review} className="space-y-3">
        <FormField label="Decision" value={action} onChange={e => setAction(e.target.value)}><option value="promote">Promote to shortlist</option><option value="reject">Reject from shortlist</option></FormField>
        <FormField label="Review reason" required minLength="10" maxLength="1000" value={reason} onChange={e => setReason(e.target.value)} hint="At least 10 characters; explain the human judgment." />
        <Message error>{error}</Message><button className={secondaryStyle} disabled={busy}>{busy ? 'Recording…' : 'Record decision'}</button>
      </form>
    </details>
    <details className="mt-4 border-t border-line pt-4">
      <summary className="cursor-pointer text-sm font-bold text-navy">Audit history ({c.audit.length})</summary>
      {c.audit.length === 0 ? <p className="mt-3 text-sm text-muted">No manual decisions yet.</p> : c.audit.map(a => <div key={a.id} className="mt-4 rounded-xl bg-paper p-4">
        <p className="text-sm font-bold text-navy">{a.action} · Recruiter #{a.recruiter_user_id} · {new Date(a.created_at).toLocaleString()}</p>
        <p className="mt-1 text-sm">{a.reason}</p><p className="mt-1 text-xs text-muted">Previous manual decision: {a.previous_action || 'none'}</p>
        <details className="mt-3"><summary className="cursor-pointer text-sm font-semibold">Evidence at decision time</summary>
          <p className="my-3 font-bold text-navy">Weighted match score: {a.evidence_at_action.match_score}/100</p>
          <p className="mb-3 text-sm">{a.evidence_at_action.explanation}</p><FactorTable factors={a.evidence_at_action.factor_breakdown} />
        </details>
      </div>)}
    </details>
  </article>
}
