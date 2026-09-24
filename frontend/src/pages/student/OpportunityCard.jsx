import FactorTable from '../../components/FactorTable'
export default function OpportunityCard({ opportunity: o, position }) {
  return <article className="rounded-3xl border border-line bg-white p-6 shadow-sm sm:p-8" aria-label={o.title}>
    <div className="flex flex-wrap items-start justify-between gap-5"><div><p className="text-xs font-bold uppercase tracking-widest text-muted">Position {position} · {o.company_name}</p><h3 className="mt-2 text-xl font-bold text-navy">{o.title}</h3><p className="mt-2 text-sm text-muted">₹{o.ctc} LPA · Drive #{o.job_id}</p><p className={'mt-3 inline-block rounded-full px-3 py-1 text-xs font-bold ' + (o.eligible ? 'bg-growth-soft text-navy' : 'bg-warning-soft text-navy')}>{o.eligible ? '✓ Meets calculated eligibility' : '⚠ Excluded by current rules'}</p></div>
      <div className="text-right"><p className="text-3xl font-bold text-navy">{o.match_score}<span className="text-sm text-muted"> /100</span></p><p className="text-xs text-muted">Weighted match score · rule-based</p></div></div>
    <p className="my-5 text-sm leading-7">{o.explanation}</p><FactorTable factors={o.factor_breakdown} />
    <div className="mt-5 rounded-2xl bg-paper p-4"><h4 className="text-sm font-bold text-navy">Eligibility requirements</h4><ul className="mt-2 flex flex-wrap gap-x-6 gap-y-2 text-xs leading-5 text-muted"><li>CGPA ≥ {o.min_cgpa}/10</li><li>Branches: {o.eligible_branches.join(', ')}</li><li>Active backlogs ≤ {o.max_backlogs}</li><li>Weighted threshold: {o.min_match_score}/100</li></ul></div>
    {!!o.missing_requirements.length && <div className="mt-4 rounded-2xl bg-warning-soft p-4"><h4 className="text-sm font-bold text-navy">Requirements & review flags</h4><ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{o.missing_requirements.map(item => <li key={item}>{item}</li>)}</ul></div>}
    <p className="mt-5 text-sm leading-6"><strong className="text-navy">Your Next Jugaad: </strong>{o.next_step}</p><p className="mt-3 text-xs leading-5 text-muted">{o.methodology}</p><p className="mt-3 text-xs font-semibold text-muted">Preparation guidance only. This is not a recruiter decision, application, or offer.</p>
  </article>
}
