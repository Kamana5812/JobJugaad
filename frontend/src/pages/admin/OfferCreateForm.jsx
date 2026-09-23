import { useCallback, useEffect, useState } from 'react'
import { createOffer, getOfferCandidates } from '../../api/offers'
import { errorMessage } from '../../api/student'
import DashboardCard from '../../components/DashboardCard'
import Pagination from '../../components/Pagination'
import { FormField, Message, buttonStyle, secondaryStyle } from '../../components/FormField'
export default function OfferCreateForm({ onSaved }) {
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState(null)
  const [interviewId, setInterviewId] = useState('')
  const [ctc, setCtc] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const load = useCallback(async () => {
    setBusy(true); setError(''); setInterviewId('')
    try { setData(await getOfferCandidates(query, offset)) } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }, [query, offset])
  useEffect(() => { load() }, [load])
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      await createOffer({ interview_id: Number(interviewId), ctc: ctc === '' ? null : Number(ctc), reason })
      setInterviewId(''); setReason(''); setCtc(''); await load(); await onSaved()
    } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  return <DashboardCard title="Create an offer" label="Selected interviews only">
    <p className="mb-4 text-sm text-muted">Record an interview as selected in Scheduling first. Each student can have one offer per drive.</p>
    <Message error>{error}</Message>
    <form className="my-4 flex flex-wrap items-end gap-3" onSubmit={e => { e.preventDefault(); setOffset(0); if (query === search) load(); else setQuery(search) }}>
      <FormField label="Find selected student" value={search} maxLength={100} onChange={e => setSearch(e.target.value)} disabled={busy} />
      <button className={secondaryStyle} disabled={busy}>Search</button>
    </form>
    <form onSubmit={submit} className="space-y-4">
      <FormField label="Selected interview" value={interviewId} onChange={e => setInterviewId(e.target.value)} required disabled={busy}>
        <option value="">Choose a student and drive</option>{data?.candidates.map(candidate => <option key={candidate.interview_id} value={candidate.interview_id}>{candidate.student_name} · {candidate.job_title} · Interview #{candidate.interview_id}</option>)}
      </FormField>
      {data?.total === 0 && <p className="text-sm text-muted">No selected interviews without an offer match this search.</p>}
      <Pagination data={data} busy={busy} onPage={setOffset} />
      <FormField label="Offer CTC (LPA, optional)" hint="Leave empty to use the drive’s advertised CTC." type="number" min="0.01" max="10000" step="0.01" value={ctc} onChange={e => setCtc(e.target.value)} disabled={busy} />
      <FormField label="Reason / supporting context" value={reason} minLength={10} maxLength={1000} onChange={e => setReason(e.target.value)} required disabled={busy} />
      <button className={buttonStyle} disabled={busy || !interviewId}>{busy ? 'Working…' : 'Create draft offer'}</button>
    </form>
  </DashboardCard>
}
