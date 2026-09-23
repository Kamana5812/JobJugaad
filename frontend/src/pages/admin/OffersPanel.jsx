import { useCallback, useEffect, useState } from 'react'
import { getOffers } from '../../api/offers'
import { errorMessage } from '../../api/student'
import OfferCard from '../../components/OfferCard'
import OfferActions from '../../components/OfferActions'
import Pagination from '../../components/Pagination'
import { Message, secondaryStyle } from '../../components/FormField'
import OfferCreateForm from './OfferCreateForm'
export default function OffersPanel({ refreshAnalytics }) {
  const [data, setData] = useState(null)
  const [offset, setOffset] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const refresh = useCallback(async () => {
    setBusy(true); setError('')
    try { setData(await getOffers(null, offset)) } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }, [offset])
  useEffect(() => { refresh() }, [refresh])
  async function saved() { await refresh(); await refreshAnalytics() }
  return <div className="space-y-6">
    <OfferCreateForm onSaved={saved} />
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-2xl font-bold text-navy">College offers</h2><button className={secondaryStyle} onClick={refresh} disabled={busy}>Refresh offers</button></div>
    <Message error>{error}</Message>{busy && <p role="status">Loading offers…</p>}
    {data?.total === 0 && <p>No offers recorded for this college yet.</p>}
    {data?.offers.map(offer => <OfferCard key={offer.id} offer={offer}><OfferActions key={offer.version} offer={offer} admin onSaved={saved} /></OfferCard>)}
    <Pagination data={data} busy={busy} onPage={setOffset} />
  </div>
}
