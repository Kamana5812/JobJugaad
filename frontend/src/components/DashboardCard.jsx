export default function DashboardCard({ title, label, children, className = '' }) {
  const numbered = typeof title === 'string' && title.match(/^(\d{2}) (.+)$/)
  return <section className={'rounded-2xl border border-line bg-white p-5 shadow-sm sm:p-6 ' + className}>
    {label && <p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">{label}</p>}
    {title && <h2 className="mb-4 mt-1 text-xl font-bold text-navy">{numbered ? <><span className="text-saffron">{numbered[1]}</span> {numbered[2]}</> : title}</h2>}
    {children}
  </section>
}
export function StatusPill({ children, warning = false, critical = false }) {
  return <span className={'inline-block rounded-full px-3 py-1 text-xs font-bold ' + (critical ? 'bg-critical-soft text-critical' : warning ? 'bg-warning-soft text-navy' : 'bg-growth-soft text-navy')}>{children}</span>
}
export const displayTime = value => value ? new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Not available'
export function localInputTime(value) {
  const date = new Date(value)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}
