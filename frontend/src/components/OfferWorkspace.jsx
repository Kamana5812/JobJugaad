import { useState } from 'react'
import OfferCard from './OfferCard'
import OfferActions from './OfferActions'
import OfferDocumentsPanel from './OfferDocumentsPanel'

export default function OfferWorkspace({ offer, admin = false, onSaved }) {
  const [fileLocked, setFileLocked] = useState(false), [stageBusy, setStageBusy] = useState(false)
  return <OfferCard offer={offer}>
    <OfferDocumentsPanel offer={offer} admin={admin} onSaved={onSaved} onLockChange={setFileLocked} disabled={stageBusy} />
    <OfferActions key={offer.version} offer={offer} admin={admin} onSaved={onSaved} disabled={fileLocked} onBusyChange={setStageBusy} />
  </OfferCard>
}
