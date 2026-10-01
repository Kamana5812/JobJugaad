import { useState } from 'react'
import { FormField, inputStyle, buttonStyle, Message } from './FormField'
import { applicationStatus } from './ApplicationCard'
import { errorMessage } from '../api/student'
const transitions = { submitted: ['under_review', 'shortlisted', 'rejected'], under_review: ['shortlisted', 'rejected'], shortlisted: ['under_review', 'rejected'] }
export default function ApplicationAction({ application, recruiter = false, onAction, onSaved, onExpired }) {
  const options = transitions[application.status] || []
  const [status, setStatus] = useState(options[0] || '')
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const id = `application-reason-${application.id}`
  if (!options.length) return <p className="text-sm text-muted">This application is closed. Its evidence and history remain available.</p>
  async function save(event) {
    event.preventDefault(); setBusy(true); setError('')
    try { await onAction({ version: application.version, reason: reason.trim(), ...(recruiter ? { status } : {}) }); await onSaved() }
    catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  return <form onSubmit={save} className="space-y-3 rounded-lg border border-line p-4">
    <h4 className="font-semibold text-navy">{recruiter ? 'Record a human review' : 'Withdraw this application'}</h4>
    <p className="text-xs leading-5 text-muted">{recruiter ? 'This decision and reason are visible to the student. Shortlisting here does not schedule an interview or issue an offer.' : 'Withdrawal closes your application; you cannot submit again to the same drive.'}</p>
    <fieldset disabled={busy} className="space-y-3">
      {recruiter && <FormField label="Application decision" required value={status} onChange={e => setStatus(e.target.value)}>{options.map(value => <option key={value} value={value}>{applicationStatus(value)}</option>)}</FormField>}
      <label htmlFor={id} className="block text-sm font-semibold text-navy">Reason / next step</label><textarea id={id} className={inputStyle} required minLength={5} maxLength={1000} rows={2} value={reason} onChange={e => setReason(e.target.value)} />
      <button className={buttonStyle} disabled={busy || reason.trim().length < 5}>{busy ? 'Saving…' : recruiter ? 'Save review decision' : 'Confirm withdrawal'}</button>
    </fieldset><Message error>{error}</Message>
  </form>
}
