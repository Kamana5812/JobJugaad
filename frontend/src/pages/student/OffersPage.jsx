import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getOffers } from '../../api/offers'
import { errorMessage } from '../../api/student'
import OfferCard from '../../components/OfferCard'
import OfferActions from '../../components/OfferActions'
import Pagination from '../../components/Pagination'
import { Message, secondaryStyle } from '../../components/FormField'
export default function OffersPage() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [offset, setOffset] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const refresh = useCallback(async () => {
    setBusy(true); setError('')
    try { setData(await getOffers(user.student_id, offset)) } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }, [user.student_id, offset])
  useEffect(() => { refresh() }, [refresh])
  return <div className="space-y-6">
    <header><p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">Career Copilot</p><h1 className="mt-2 text-3xl font-bold text-navy">My offers</h1><p className="mt-3 text-muted">Track each stage, record your response, and see what comes next.</p></header>
    <button className={secondaryStyle} onClick={refresh} disabled={busy}>Refresh offers</button><Message error>{error}</Message>
    {busy && <p role="status">Loading offers…</p>}
    {data?.total === 0 && <p className="rounded-2xl border border-line bg-white p-6">No offers recorded yet. Your placement cell creates an offer after a selected interview.</p>}
    {data?.offers.map(offer => <OfferCard key={offer.id} offer={offer}><OfferActions key={offer.version} offer={offer} onSaved={refresh} /></OfferCard>)}
    <Pagination data={data} busy={busy} onPage={setOffset} />
  </div>
}
