import example from '../../assets/matching-example.json'
export default function MatchingExample() {
  return <article className="overflow-hidden rounded-3xl border border-line bg-white shadow-sm">
    <div className="border-b border-line p-6 sm:p-8"><p className="text-xs font-bold uppercase tracking-widest text-muted">Saved synthetic example · not a real candidate</p>
      <h3 className="mt-3 text-xl font-bold text-navy">{example.student} → {example.job_title}</h3>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-4"><p className="text-sm text-muted">Weighted match score <strong className="ml-2 text-3xl text-navy">{example.match_score}<span className="text-base font-medium">/100</span></strong></p><span className="rounded-full bg-warning-soft px-4 py-1 text-sm font-semibold text-navy">Below Threshold</span></div>
      <p className="mt-4 text-sm leading-6 text-ink">{example.explanation}</p>
    </div>
    <div className="p-6 sm:p-8"><p className="text-xs font-bold uppercase tracking-widest text-muted">Every contributing factor</p>
      <div className="mt-4 space-y-5">{example.factor_breakdown.map(f => <div key={f.key}>
        <div className="flex justify-between gap-4 text-sm font-semibold text-navy"><span>{f.label}</span><span className="tabular-nums">{f.contribution.toFixed(2)} pts</span></div>
        <div aria-hidden="true" className="mt-2 h-1.5 overflow-hidden rounded-full bg-paper"><div className="h-full rounded-full bg-saffron" style={{ width: `${f.value}%` }} /></div>
        <p className="mt-1 text-xs leading-5 text-muted">{f.value}/100 × {f.weight}% weight. {f.evidence}</p>
      </div>)}</div>
      <div className="mt-6 rounded-2xl bg-growth-soft p-4"><h4 className="text-sm font-bold text-navy">Your Next Jugaad</h4><p className="mt-1 text-sm text-ink">{example.next_step}</p></div>
      <details className="mt-5 text-xs leading-5 text-muted"><summary className="cursor-pointer rounded py-1 font-semibold text-navy focus-visible:outline-2">All gaps & how this rule works</summary><ul className="my-3 list-disc pl-4">{example.missing_requirements.map(item => <li key={item}>{item}</li>)}</ul><p>{example.methodology}</p><p className="mt-2">Source: frozen Phase 4 evaluation, synthetic profile 301. This is an illustration of the rule, not validated hiring accuracy.</p></details>
    </div>
  </article>
}
