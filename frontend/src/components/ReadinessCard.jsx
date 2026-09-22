export default function ReadinessCard({ readiness, dirty }) {
  const healthy = ['Ready', 'Highly Employable'].includes(readiness.band)
  return <section aria-labelledby="readiness-title" className="overflow-hidden rounded-3xl border border-line bg-white shadow-sm">
    <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[240px_1fr]">
      <div>
        <p className="text-xs font-bold uppercase tracking-widest text-muted">Career Copilot · Readiness</p>
        <h2 id="readiness-title" className="mt-2 text-2xl font-bold text-navy">Kitne Ready Ho?</h2>
        <p className="mt-4 text-6xl font-bold tracking-tight text-navy">{readiness.score}<span className="text-xl font-medium text-muted"> / 100</span></p>
        <span className={`mt-4 inline-block rounded-full px-3 py-1 text-sm font-semibold ${healthy ? 'bg-[#E2F3E9] text-[#286844]' : 'bg-[#FDF0E3] text-[#914005]'}`}>{readiness.band}</span>
        <p className="mt-4 text-xs text-muted">Based on your saved profile.</p>
        {dirty && <p className="mt-2 text-sm font-semibold text-[#914005]">Unsaved changes — save to recalculate.</p>}
      </div>
      <div>
        <p className="text-lg font-medium leading-8 text-navy">{readiness.explanation}</p>
        <div className="mt-5 rounded-2xl bg-paper p-4">
          <h3 className="text-sm font-bold text-navy">Your Next Jugaad</h3>
          <p className="mt-1 text-sm leading-6 text-muted">{readiness.next_step}</p>
        </div>
      </div>
    </div>
    <div className="overflow-x-auto border-t border-line">
      <table className="w-full min-w-[580px] text-left text-sm">
        <caption className="px-6 py-4 text-left font-bold text-navy">Why this score? Every contributing factor.</caption>
        <thead className="bg-paper text-xs uppercase tracking-wide text-muted"><tr>
          <th className="px-6 py-3">Factor &amp; evidence</th><th className="px-3 py-3">Input / 100</th>
          <th className="px-3 py-3">Weight</th><th className="px-6 py-3 text-right">Points</th>
        </tr></thead>
        <tbody>{readiness.breakdown.map((factor) => <tr key={factor.key} className="border-t border-line">
          <th scope="row" className="px-6 py-4 font-normal"><span className="font-semibold text-navy">{factor.label}</span>
            <span className="mt-1 block max-w-lg text-xs leading-5 text-muted">{factor.evidence}</span></th>
          <td className="px-3 py-4">{factor.missing ? 'Not recorded' : factor.value}</td>
          <td className="px-3 py-4">{factor.weight}%</td><td className="px-6 py-4 text-right font-bold text-navy">{factor.contribution.toFixed(2)}</td>
        </tr>)}</tbody>
        <tfoot className="border-t border-line bg-paper font-semibold text-navy"><tr><th colSpan="3" className="px-6 py-3">Weighted total before whole-number rounding</th><td className="px-6 py-3 text-right">{readiness.raw_score.toFixed(2)}</td></tr></tfoot>
      </table>
    </div>
    <p className="border-t border-line px-6 py-4 text-xs leading-5 text-muted">{readiness.methodology} This guides preparation; it does not decide placement eligibility.</p>
  </section>
}
