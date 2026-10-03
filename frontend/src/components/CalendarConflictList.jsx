import { displayTime } from './DashboardCard'

export default function CalendarConflictList({ items = [] }) {
  if (!items.length) return null
  return <div className="mt-3 rounded-lg border border-saffron-deep/30 bg-warning-soft p-3">
    <h4 className="text-sm font-semibold text-navy">Calendar constraints</h4>
    <ul className="mt-2 space-y-2 text-sm">{items.map((item, index) => <li key={`${item.constraint_id ?? 'policy'}-${item.kind}-${index}`}>
      <p>{item.explanation}</p>
      {item.starts_at && item.ends_at && <p className="mt-1 text-xs text-muted">{displayTime(item.starts_at)} – {displayTime(item.ends_at)}</p>}
    </li>)}</ul>
  </div>
}
