import DashboardCard, { displayTime, StatusPill } from './DashboardCard'
export const offerStages = [['offer_letter_status', 'Offer letter'], ['documents_status', 'Documents'], ['verification_status', 'Verification'], ['acceptance_status', 'Acceptance'], ['joining_status', 'Joining']]
const human = value => value.replaceAll('_', ' ')
export default function OfferCard({ offer, children }) {
  return <DashboardCard title={offer.job_title} label={offer.is_synthetic ? 'Synthetic demonstration offer' : 'Offer tracking'}>
    <p className="text-sm text-muted">{offer.company_name} · {offer.student_name} · Offer #{offer.id}</p>
    <p className="mt-2 font-bold text-navy">CTC: {offer.ctc.toFixed(2)} LPA</p>
    <dl className="my-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{offerStages.map(([key, label]) => <div key={key} className="rounded-xl bg-paper p-3">
      <dt className="mb-2 text-xs font-bold text-muted">{label}</dt><dd><StatusPill warning={!['issued', 'submitted', 'verified', 'accepted', 'joined'].includes(offer[key])}>{human(offer[key])}</StatusPill></dd>
    </div>)}</dl>
    <ul className="list-disc space-y-1 pl-5 text-sm">{offer.next_steps.map(step => <li key={step}>{step}</li>)}</ul>
    <p className="mt-4 text-xs leading-5 text-muted">{offer.methodology}</p>
    {children}
    <details className="mt-5 rounded-xl border border-line p-3 text-sm"><summary className="cursor-pointer font-bold text-navy">Stage history ({offer.audit.length})</summary>
      <ol className="mt-3 space-y-4">{offer.audit.map(event => <li key={event.id} className="border-t border-line pt-3">
        <p className="font-semibold">{human(event.action)} · {displayTime(event.created_at)} · {event.actor_user_id === null ? 'Synthetic import' : `Account #${event.actor_user_id}`}</p>
        <p className="mt-1">{event.reason}</p>
        {event.snapshot.after && <p className="mt-2 text-xs text-muted">{offerStages.map(([key, label]) => `${label}: ${human(event.snapshot.after[key] || 'not recorded')}`).join(' · ')}</p>}
      </li>)}</ol>
    </details>
  </DashboardCard>
}
