import FactorTable from './FactorTable'
import TextEvidence from './TextEvidence'
export const applicationStatus = value => value.replaceAll('_', ' ')
export default function ApplicationCard({ application: a, children }) {
  const e = a.evidence
  return <article className="space-y-5 rounded-xl border border-line bg-white p-5 sm:p-6">
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="text-xs text-muted">Application #{a.id} · {a.company_name}</p><h3 className="mt-1 text-lg font-bold text-navy">{a.job_title}</h3><p className="mt-1 text-sm text-muted">{a.student_name} · Submitted {new Date(a.created_at).toLocaleString()}</p></div>
      <span className="rounded-full bg-paper px-3 py-1 text-sm font-semibold capitalize text-navy">{applicationStatus(a.status)}</span>
    </div>
    {a.cover_note && <p className="whitespace-pre-wrap rounded-lg bg-paper p-4 text-sm text-ink">{a.cover_note}</p>}
    <p className="text-sm leading-6 text-muted">{a.explanation}</p>
    <div className="rounded-lg bg-paper p-4"><p className="text-sm font-semibold text-navy">Submission-time match: {e.match_score}/100 · {e.eligible ? 'Meets weighted rules' : 'Gaps for human review'}</p>
      <p className="mt-2 text-sm leading-6 text-ink">{e.explanation}</p><p className="mt-2 text-sm text-navy">Next step: {e.next_step}</p></div>
    <FactorTable factors={e.factor_breakdown} />
    <TextEvidence evidence={e.text_evidence} />
    {e.missing_requirements.length > 0 && <div><h4 className="text-sm font-bold text-navy">Recorded requirements to review</h4><ul className="mt-2 list-inside list-disc space-y-1 text-sm text-muted">{e.missing_requirements.map((gap, i) => <li key={i}>{gap}</li>)}</ul></div>}
    <p className="text-xs leading-5 text-muted">{e.methodology}</p>
    {children}
    <details className="border-t border-line pt-4"><summary className="cursor-pointer text-sm font-semibold text-navy">Status history ({a.history.length})</summary>
      <ol className="mt-3 space-y-3">{a.history.map(event => <li key={event.id} className="rounded-lg bg-paper p-3 text-sm"><p className="font-semibold capitalize text-navy">{event.previous_status ? applicationStatus(event.previous_status) + ' → ' : ''}{applicationStatus(event.status)}</p><p className="mt-1 text-ink">{event.reason}</p><time className="mt-1 block text-xs text-muted">{new Date(event.created_at).toLocaleString()}</time></li>)}</ol>
    </details>
  </article>
}
