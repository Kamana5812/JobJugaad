import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import DashboardCard from './DashboardCard'
export default function ConversionChart({ title, rows }) {
  return <DashboardCard title={title} label="Shortlist conversion">
    <p className="mb-4 text-sm text-muted">Distinct students shortlisted for at least one drive, divided by students recorded in each group. Human overrides are included.</p>
    {rows.length ? <>
      <div className="h-72 min-w-0" role="img" aria-label={title + ': recorded and shortlisted students; exact values in the table below.'}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 32, left: -16 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E6EC" />
            <XAxis dataKey="name" tick={{ fill: '#5B6B7D', fontSize: 11 }} angle={-30} textAnchor="end" interval={0} height={52} />
            <YAxis allowDecimals={false} tick={{ fill: '#5B6B7D', fontSize: 11 }} />
            <Tooltip /><Legend />
            <Bar dataKey="total_students" name="Recorded students" fill="#0F2A4A" radius={[3, 3, 0, 0]} />
            <Bar dataKey="shortlisted_students" name="Shortlisted students" fill="#F2802E" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm">
        <caption className="sr-only">{title} shortlist conversion</caption>
        <thead className="border-b border-line text-muted"><tr><th className="py-2">Group</th><th>Shortlisted / recorded</th><th>Conversion</th></tr></thead>
        <tbody>{rows.map(row => <tr key={row.name} className="border-b border-line"><th className="py-2 font-medium">{row.name}</th>
          <td>{row.shortlisted_students} / {row.total_students}</td><td>{row.conversion_percent === null ? 'Not available' : row.conversion_percent + '%'}</td></tr>)}</tbody>
      </table></div>
    </> : <p className="text-sm text-muted">No recorded students in this group yet.</p>}
  </DashboardCard>
}
