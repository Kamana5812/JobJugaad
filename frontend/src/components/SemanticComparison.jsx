import { useState } from 'react'
import { compareSemantics } from '../api/nlp'
import { errorMessage } from '../api/student'
import { Message, secondaryStyle } from './FormField'

export default function SemanticComparison({ studentId, jobId, applicationId, admin, onExpired }) {
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function compare() {
    setBusy(true); setError(''); setResult(null)
    try { setResult(await compareSemantics({ studentId, jobId, applicationId, admin })) }
    catch (failure) { if (failure.response?.status === 401 && onExpired) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <section className="space-y-3 rounded-xl border border-line bg-paper p-4">
    <h4 className="font-bold text-navy">Semantic evidence · optional</h4>
    <p className="text-xs leading-5 text-muted">Compare meaning using a pretrained sentence-embedding model running locally in the backend. Requires a saved job description. This does not alter eligibility, weighted score, rank or shortlist decisions.</p>
    <button className={secondaryStyle} disabled={busy} onClick={compare}>{busy ? 'Comparing evidence…' : 'Compare semantic evidence'}</button>
    <Message error>{error}</Message>
    {result && <div className="space-y-3"><p className="font-bold text-navy">Semantic comparison {result.score}/100</p><p className="text-sm leading-6">{result.explanation}</p>
      <dl className="space-y-2 text-sm">{result.factor_breakdown.map((factor, i) => <div key={i} className="flex justify-between gap-4"><dt>{factor.term}</dt><dd>{factor.contribution} points</dd></div>)}</dl><p className="text-xs leading-5 text-muted">{result.methodology}</p></div>}
  </section>
}
