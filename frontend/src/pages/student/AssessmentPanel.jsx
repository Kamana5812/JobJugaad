import { useEffect, useState } from 'react'
import { getAssessments } from '../../api/assessments'
import { errorMessage } from '../../api/student'
import AssessmentRecords from '../../components/AssessmentRecords'
import { Message, secondaryStyle } from '../../components/FormField'

export default function AssessmentPanel({ studentId }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [offset, setOffset] = useState(0)
  async function load() {
    setBusy(true); setError('')
    try { setData(await getAssessments(studentId, {offset, limit:20})) }
    catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  useEffect(() => { load() }, [studentId, offset])
  return <section id="assessment-evidence" className="scroll-mt-6 space-y-5 rounded-xl border border-line bg-white p-6">
    <h2 className="text-xl font-bold text-navy">Assessment evidence</h2>
    <p className="text-sm leading-6 text-muted">Your college can record external assessment results with a source and review context. You cannot mark your own scores verified. These are staff declarations, not independently authenticated exams. Readiness, matching and support still use your self-reported profile inputs.</p>
    <button disabled={busy} className={secondaryStyle} onClick={load}>{busy ? 'Loading…' : 'Refresh evidence'}</button>
    <Message error>{error}</Message>
    {data && <><AssessmentRecords items={data.items} />{!data.items.length && <p className="text-sm text-muted">No staff-recorded assessments on this page. No result is inferred from your profile.</p>}
      <div className="flex items-center gap-3"><button className={secondaryStyle} disabled={busy || offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>Previous</button>
        <span className="text-sm text-muted">{data.total} records · page {offset / 20 + 1}</span>
        <button className={secondaryStyle} disabled={busy || offset + 20 >= data.total} onClick={() => setOffset(offset + 20)}>Next</button></div></>}
  </section>
}
