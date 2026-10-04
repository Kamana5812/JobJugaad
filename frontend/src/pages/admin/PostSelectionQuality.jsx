const checks = {
  offers_without_history: 'Offers without audit history', invalid_offer_history_events: 'Offer events with incomplete or invalid stage snapshots',
  invalid_selection_history_events: 'Interview events with incomplete or invalid selection snapshots', withdrawn_without_issuance_evidence: 'Withdrawn offers without issuance evidence',
  accepted_without_issuance_evidence: 'Accepted offers without issuance evidence', selection_from_linked_offer: 'Pairs with selection evidenced by a linked offer',
  selection_from_history: 'Pairs with selection evidenced by interview history',
  offers_with_mismatched_interview: 'Offers with a mismatched linked interview', historical_selection_no_current_selection: 'Pairs with historical selection but no current selected interview',
}
export default function PostSelectionQuality({ quality }) {
  return <details className="rounded-xl border border-line bg-paper p-4 text-sm">
    <summary className="cursor-pointer font-semibold text-navy">Evidence coverage and missing history</summary>
    <p className="mt-3 text-xs leading-5 text-muted">Missing audit evidence is shown explicitly. A linked offer is evidence of the recorded selection prerequisite, not independent proof of employment. Evidence sources may overlap.</p>
    <dl className="mt-3 divide-y divide-line">{Object.entries(checks).map(([key, label]) => <div key={key} className="flex flex-wrap justify-between gap-2 py-2"><dt>{label}</dt><dd className="font-medium text-navy">{quality[key]}</dd></div>)}</dl>
  </details>
}
