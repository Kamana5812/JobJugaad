import { useId } from 'react'

export const inputStyle = 'w-full rounded-xl border border-line bg-white px-3 py-2.5 text-ink outline-none focus:border-navy focus:ring-2 focus:ring-navy/15 disabled:bg-paper'
export const buttonStyle = 'inline-flex items-center justify-center rounded-xl bg-saffron px-5 py-3 text-sm font-bold text-navy-dark transition hover:bg-saffron-deep focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-navy disabled:cursor-wait disabled:opacity-60'
export const secondaryStyle = 'rounded-xl border border-line bg-white px-4 py-2 text-sm font-semibold text-navy hover:bg-paper focus-visible:outline-2 focus-visible:outline-navy'
export function FormField({ label, hint, children, ...props }) {
  const id = useId()
  return <div>
    <label htmlFor={id} className="mb-1.5 block text-sm font-semibold text-navy">{label}</label>
    {children ? <select id={id} className={inputStyle} aria-describedby={hint ? id + '-hint' : undefined} {...props}>{children}</select>
      : <input id={id} className={inputStyle} aria-describedby={hint ? id + '-hint' : undefined} {...props} />}
    {hint && <p id={id + '-hint'} className="mt-1.5 text-xs leading-5 text-muted">{hint}</p>}
  </div>
}
export function Message({ error, children }) {
  return children ? <p role={error ? 'alert' : 'status'} className={`rounded-xl border p-3 text-sm ${error ? 'border-critical/30 bg-critical-soft text-critical' : 'border-growth/30 bg-growth-soft text-navy'}`}>{children}</p> : null
}
