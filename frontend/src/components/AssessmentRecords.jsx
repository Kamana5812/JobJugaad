import { useState } from 'react'
import { FormField, buttonStyle } from './FormField'

export default function AssessmentRecords({ items, onWithdraw, busy }) {
  const [reasons, setReasons] = useState({})
  return <div className="space-y-4">{items.map(row => <article key={row.id} className="rounded-xl border border-line p-5">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><h3 className="font-semibold text-navy">{row.title} · {row.student_name}</h3>
        <p className="mt-1 text-sm text-muted">{row.kind}{row.skill_name ? ` · ${row.skill_name}` : ''} · Student #{row.student_id} · Record #{row.id}</p></div>
      <span className={'rounded-full px-3 py-1 text-xs font-semibold ' + (row.withdrawn_at ? 'bg-critical-soft text-critical' : 'bg-growth-soft text-growth')}>
        {row.withdrawn_at ? 'Withdrawn · history retained' : 'Staff-recorded declaration'}</span>
    </div>
    <p className="mt-4 text-sm leading-6 text-ink">{row.explanation}</p>
    <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
      {[["Original result", `${row.score} / ${row.maximum}`], ["Source / provider", row.source], ["Result reference", row.reference],
        ["Assessed", new Date(row.assessed_on).toLocaleString()], ["Recorded", new Date(row.created_at).toLocaleString()],
        ["Recorded by", `College administrator #${row.recorded_by}`], ["Review context", row.reason]].map(([label,value]) =>
        <div key={label}><dt className="text-muted">{label}</dt><dd className="mt-1 break-words text-ink">{value}</dd></div>)}
    </dl>
    {row.withdrawn_at && <p className="mt-4 text-sm text-critical">Withdrawn by administrator #{row.withdrawn_by} on {new Date(row.withdrawn_at).toLocaleString()}: {row.withdrawal_reason}</p>}
    {onWithdraw && !row.withdrawn_at && <details className="mt-4 text-sm"><summary className="cursor-pointer font-semibold text-navy">Withdraw an incorrect record</summary>
      <form className="mt-3 space-y-3" onSubmit={async event => { event.preventDefault(); await onWithdraw(row.id, reasons[row.id] || '') }}>
        <FormField label={`Withdrawal reason for record #${row.id}`} required minLength={10} maxLength={1000}
          value={reasons[row.id] || ''} onChange={event => setReasons({ ...reasons, [row.id]:event.target.value })} />
        <button disabled={busy} className={buttonStyle}>Withdraw record · keep history</button>
      </form></details>}
  </article>)}</div>
}
