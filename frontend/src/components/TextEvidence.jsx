export default function TextEvidence({ evidence }) {
  if (!evidence) return null
  return <details className="rounded-xl border border-line p-4"><summary className="cursor-pointer text-sm font-bold text-navy">Separate lexical comparison · {evidence.score}/100</summary>
    <p className="mt-3 text-sm">{evidence.explanation}</p>
    <dl className="mt-3 space-y-1 text-sm">{evidence.factor_breakdown.map(factor => <div key={factor.term} className="flex justify-between gap-3"><dt>{factor.term}</dt><dd>{factor.contribution} points</dd></div>)}</dl>
    {evidence.factor_breakdown.length === 0 && <p className="mt-2 text-sm">No shared vocabulary contributes to this comparison.</p>}
    <p className="mt-3 text-xs text-muted">{evidence.methodology}</p>
  </details>
}
