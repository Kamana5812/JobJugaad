import Pagination from '../../components/Pagination'

const outcomes = { withdrawn: 'Offer withdrawn', declined: 'Offer declined', not_joined: 'Recorded non-joining' }
const sources = { recorded_action: 'Recorded action reason', synthetic_import: 'Synthetic import note', missing: 'No audited reason recorded' }
export default function PostSelectionReasons({ data, busy, onPage }) {
  return <section aria-label="Recorded closure reasons"><h3 className="font-semibold text-navy">Withdrawal, decline and non-joining reasons</h3>
    <p className="mt-2 text-sm leading-6 text-muted">Exact recorded text is grouped by outcome and evidence source. It is not an inferred cause or automated classification. Synthetic import notes describe fictional records; missing reasons remain unknown.</p>
    {!data.reason_total ? <p className="mt-3 text-sm text-muted">No terminal closure reasons in this view.</p> : <>
      <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[580px] text-left text-sm">
        <caption className="sr-only">Exact recorded closure reasons with evidence source and student–drive pair counts</caption>
        <thead className="border-b border-line text-muted"><tr><th className="py-2 pr-4">Outcome</th><th className="pr-4">Recorded text / source</th><th>Pairs</th></tr></thead>
        <tbody>{data.reasons.map((row, index) => <tr key={data.offset + index} className="border-b border-line align-top">
          <th scope="row" className="py-3 pr-4 font-medium text-navy">{outcomes[row.closure]}</th>
          <td className="py-3 pr-4"><p className="max-w-lg whitespace-pre-wrap break-words">{row.reason || 'No audited reason recorded'}</p><p className="mt-1 text-xs text-muted">{sources[row.reason_source]}</p></td>
          <td className="py-3">{row.count}<p className="mt-1 text-xs text-muted">{row.recorded_count} recorded · {row.synthetic_count} synthetic/archive</p></td>
        </tr>)}</tbody>
      </table></div>
      <div className="mt-4"><Pagination data={{ total: data.reason_total, offset: data.offset, limit: data.limit }} busy={busy} onPage={onPage} /></div>
    </>}
  </section>
}
