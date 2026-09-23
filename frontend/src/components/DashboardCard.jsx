export default function DashboardCard({ title, label, children, className = '' }) {
  return <section className={'rounded-2xl border border-line bg-white p-5 shadow-sm sm:p-6 ' + className}>
    {label && <p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">{label}</p>}
    {title && <h2 className="mb-4 mt-1 text-xl font-bold text-navy">{title}</h2>}
    {children}
  </section>
}
export function StatusPill({ children, warning = false }) {
  return <span className={'inline-block rounded-full px-3 py-1 text-xs font-bold ' + (warning ? 'bg-[#FDF0E3] text-[#994609]' : 'bg-[#E2F3E9] text-navy')}>{children}</span>
}
export const displayTime = value => value ? new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Not available'
export function localInputTime(value) {
  const date = new Date(value)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}
