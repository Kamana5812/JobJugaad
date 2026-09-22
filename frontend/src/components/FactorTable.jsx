export default function FactorTable({ factors }) {
  return <div className="overflow-x-auto rounded-xl border border-line">
    <table className="w-full text-left text-sm">
      <caption className="sr-only">Full factor breakdown: normalized values, weights, points and evidence</caption>
      <thead className="bg-paper text-xs text-muted"><tr><th className="p-3">Factor / evidence</th><th className="p-3">Value /100</th><th className="p-3">Weight</th><th className="p-3">Points</th></tr></thead>
      <tbody>{factors.map(f => <tr key={f.key} className="border-t border-line">
        <th scope="row" className="min-w-48 p-3 font-semibold text-navy">{f.label}<p className="mt-1 text-xs font-normal leading-5 text-muted">{f.evidence}{f.missing ? ' Missing evidence contributes zero where applicable.' : ''}</p></th>
        <td className="p-3">{f.value}</td><td className="p-3">{f.weight}%</td><td className="p-3 font-bold text-navy">{f.contribution}</td>
      </tr>)}</tbody>
    </table>
  </div>
}
