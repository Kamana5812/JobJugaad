import { useState } from 'react'
import { FormField, buttonStyle, Message } from '../../components/FormField'
import DashboardCard, { displayTime, StatusPill } from '../../components/DashboardCard'
import AuditTrail from '../../components/AuditTrail'
import { reviewSupport } from '../../api/admin'
import { errorMessage } from '../../api/student'
export default function SupportCard({ student, onReviewed }) {
  const [action, setAction] = useState('reviewed')
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('')
    try { onReviewed(await reviewSupport(student.id, { action, reason })); setReason('') }
    catch (failure) { setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <DashboardCard label="Thoda Aur Jugaad Chahiye">
    <div className="mt-2 flex flex-wrap items-center justify-between gap-3"><h3 className="text-xl font-bold text-navy">{student.student_name} <span className="text-sm font-normal text-muted">#{student.student_id}</span></h3>
      <StatusPill warning={student.review_status === 'active'}>{student.review_status === 'active' ? 'Awaiting human review' : student.review_status}</StatusPill></div>
    <p className="mt-4 text-lg font-bold text-navy">{student.score}/3 support indicators met</p>
    <p className="mt-2 text-sm">{student.explanation}</p>
    <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm">
      <caption className="sr-only">Support indicator breakdown for {student.student_name}</caption>
      <thead className="border-b border-line text-muted"><tr><th className="p-2">Named factor</th><th className="p-2">Rule</th><th className="p-2">Contribution</th><th className="p-2">Evidence and explanation</th></tr></thead>
      <tbody>{student.contributing_factors.map(factor => <tr key={factor.key} className="border-b border-line align-top">
        <th className="p-2 font-semibold text-navy">{factor.label}</th><td className="p-2">{factor.threshold}</td>
        <td className="p-2">{factor.contribution} / 1 · {factor.triggered ? 'Met' : 'Not met'}</td><td className="min-w-56 p-2">{factor.explanation}</td>
      </tr>)}</tbody>
    </table></div>
    <h4 className="mt-5 font-bold text-navy">Recommended support</h4>
    <ul className="mt-2 space-y-2 text-sm">{student.recommendation.map(item => <li key={item.category}><strong>{item.category}:</strong> {item.action}</li>)}</ul>
    <p className="mt-4 text-xs leading-5 text-muted">{student.methodology}<br />Evidence last calculated {displayTime(student.evaluated_at)}. Rerun checks after profile or attendance changes.</p>
    <form onSubmit={submit} className="mt-5 space-y-3 border-t border-line pt-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField label={'Review action for student #' + student.student_id} value={action} onChange={event => setAction(event.target.value)}>
          <option value="reviewed">Reviewed — support discussed</option><option value="dismissed">Dismiss — context does not support flag</option><option value="active">Reopen for review</option>
        </FormField>
        <FormField label={'Review reason for student #' + student.student_id} required minLength="10" maxLength="1000" value={reason} onChange={event => setReason(event.target.value)} />
      </div>
      <Message error>{error}</Message><button className={buttonStyle} disabled={busy}>{busy ? 'Saving…' : 'Save support review'}</button>
    </form>
    <AuditTrail events={student.audit} />
  </DashboardCard>
}
