import { displayTime } from './DashboardCard'
export default function AuditTrail({ events }) {
  return <details className="mt-4 rounded-xl border border-line p-3 text-sm">
    <summary className="cursor-pointer font-semibold text-navy">Review history ({events.length})</summary>
    {!events.length && <p className="mt-3 text-muted">No review actions recorded yet.</p>}
    <ol className="mt-3 space-y-3">{events.map(event => <li key={event.id} className="border-t border-line pt-3">
      <p className="font-semibold text-navy">{event.action} · {displayTime(event.created_at)} · Admin #{event.actor_user_id}</p>
      <p>{event.reason}</p>
    </li>)}</ol>
  </details>
}
