import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export default function PostSelectionStages({ rows }) {
  return <section aria-label="Cumulative post-selection funnel">
    <h3 className="font-semibold text-navy">Selected → Issued → Accepted → Accepted and verified → Joined</h3>
    <p className="mt-2 text-sm leading-6 text-muted">Each stage requires all earlier recorded milestones for the same pair. Acceptance and verification can happen in either order; this layout does not claim a timing sequence. Historical progress remains visible after a closure.</p>
    {rows.some(row => row.count > 0) && <div className="my-4 h-80 min-w-0" role="img" aria-label="Student–drive pairs that reached every milestone up to each stage; exact values and denominators in the table below.">
      <ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E6EC" />
        <XAxis type="number" allowDecimals={false} tick={{ fill: '#5B6B7D', fontSize: 11 }} />
        <YAxis type="category" dataKey="label" width={150} tick={{ fill: '#5B6B7D', fontSize: 11 }} />
        <Tooltip formatter={value => [value, 'Student–drive pairs']} />
        <Bar dataKey="count" name="Student–drive pairs" fill="#0F2A4A" radius={[0, 3, 3, 0]} />
      </BarChart></ResponsiveContainer>
    </div>}
    <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm">
      <caption className="sr-only">Cumulative milestones, previous-stage denominators and records that have not reached the next stage</caption>
      <thead className="border-b border-line text-muted"><tr><th className="py-2 pr-4">Cumulative milestone</th><th className="pr-4">Pairs / students</th><th className="pr-4">From previous stage</th><th>Not yet reached</th></tr></thead>
      <tbody>{rows.map(row => <tr key={row.key} className="border-b border-line align-top">
        <th scope="row" className="py-3 pr-4 font-medium text-navy">{row.label}<p className="mt-1 max-w-sm text-xs font-normal leading-5 text-muted">{row.explanation}</p></th>
        <td className="py-3 pr-4">{row.count} pairs<br /><span className="text-xs text-muted">{row.distinct_students} distinct students</span></td>
        <td className="py-3 pr-4">{row.previous_count === null ? 'Cohort baseline' : <>{row.count} / {row.previous_count}<br /><span className="text-xs text-muted">{row.conversion_percent === null ? 'Rate unavailable: no previous-stage pairs' : row.conversion_percent + '% of previous-stage pairs'}</span></>}</td>
        <td className="py-3">{row.previous_count === null ? '—' : <>{row.not_reached_from_previous} pairs<br /><span className="text-xs text-muted">{row.pending_from_previous} without a recorded offer closure<br />{row.closed_from_previous} with a recorded offer closure</span></>}</td>
      </tr>)}</tbody>
    </table></div>
    <p className="mt-3 text-xs leading-5 text-muted">Not yet reached includes pairs with and without a recorded terminal offer closure. No recorded closure does not mean active progress or a dropout; a closed record is not a finding about a student's future.</p>
  </section>
}
