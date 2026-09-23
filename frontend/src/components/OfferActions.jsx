import { useState } from 'react'
import { FormField, Message, buttonStyle } from './FormField'
import { respondToOffer, updateOffer } from '../api/offers'
import { errorMessage } from '../api/student'
function availableActions(offer, admin) {
  if (offer.offer_letter_status === 'withdrawn' || offer.acceptance_status === 'declined' || offer.joining_status !== 'pending') return []
  const actions = []
  if (admin) {
    if (offer.offer_letter_status === 'draft') actions.push(['offer_letter_status:issued', 'Record letter issued'])
    actions.push(['offer_letter_status:withdrawn', 'Withdraw offer'])
    if (offer.offer_letter_status === 'issued' && offer.documents_status === 'submitted') {
      actions.push(['documents_status:changes_requested', 'Request document corrections'])
      if (offer.verification_status !== 'verified') actions.push(['verification_status:verified', 'Record documents verified'])
      if (offer.verification_status !== 'rejected') actions.push(['verification_status:rejected', 'Record verification rejected'])
    }
    if (offer.offer_letter_status === 'issued' && offer.acceptance_status === 'accepted' && offer.verification_status === 'verified') {
      actions.push(['joining_status:joined', 'Record joined'], ['joining_status:not_joined', 'Record did not join'])
    }
  } else if (offer.offer_letter_status === 'issued') {
    if (['pending', 'changes_requested'].includes(offer.documents_status)) actions.push(['submit_documents', 'Record documents submitted'])
    if (offer.acceptance_status === 'pending') actions.push(['accept', 'Accept offer'], ['decline', 'Decline offer'])
  }
  return actions
}
export default function OfferActions({ offer, admin = false, onSaved }) {
  const actions = availableActions(offer, admin)
  const [choice, setChoice] = useState('')
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const input = { version: offer.version, reason }
      if (admin) { const [stage, value] = choice.split(':'); await updateOffer(offer.id, { ...input, stage, value }) }
      else await respondToOffer(offer.student_id, offer.id, { ...input, action: choice })
      setReason(''); setChoice(''); await onSaved()
    } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  if (!actions.length) return null
  return <form onSubmit={submit} className="mt-5 space-y-3 border-t border-line pt-5">
    <Message error>{error}</Message>
    <FormField label="Record an action" value={choice} onChange={e => setChoice(e.target.value)} required disabled={busy}>
      <option value="">Choose an action</option>{actions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
    </FormField>
    <FormField label="Reason / supporting context" hint="This action and reason will remain in the offer history. Exchange documents through your college’s agreed channel." value={reason} onChange={e => setReason(e.target.value)} minLength={10} maxLength={1000} required disabled={busy} />
    <button className={buttonStyle} disabled={busy || !choice}>{busy ? 'Saving…' : 'Confirm action'}</button>
  </form>
}
