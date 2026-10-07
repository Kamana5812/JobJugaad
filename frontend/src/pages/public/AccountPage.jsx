import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { exportAccount, getDataRequests, requestDeletion, withdrawDeletion } from '../../api/accountData'
import { errorMessage } from '../../api/student'
import { FormField, Message, buttonStyle, secondaryStyle } from '../../components/FormField'

export default function AccountPage() {
  const { user, logout } = useAuth()
  const [rows, setRows] = useState([])
  const [reason, setReason] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  useEffect(() => { let active = true; getDataRequests().then(data => { if (active) setRows(data) }).catch(e => { if (active) setError(errorMessage(e)) }); return () => { active = false } }, [])
  async function action(fn) {
    setBusy(true); setError(''); setMessage('')
    try { await fn() } catch (failure) { setError(errorMessage(failure)) } finally { setBusy(false) }
  }
  async function download() {
    const data = await exportAccount()
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a'); link.href = url; link.download = 'jobjugaad-account-export.json'; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000); setMessage('Your account export was prepared. Keep the downloaded file private.')
  }
  async function submit(event) {
    event.preventDefault()
    await action(async () => { await requestDeletion({ reason, confirmation }); setRows(await getDataRequests()); setReason(''); setConfirmation(''); setMessage('Your deletion request is queued for college review. No data has been erased yet.') })
  }
  return <section className="mx-auto max-w-3xl space-y-6">
    <h1 className="text-3xl font-bold text-navy">Account & data</h1>
    {user.role === 'recruiter' && !user.is_demo && <Link to="/recruiter/workspaces" className="font-semibold text-navy underline">Manage college workspaces →</Link>}
    <p>{user.email} · Your college workspace</p><Link to="/privacy" className="text-navy underline">Privacy and retention notice</Link>
    <Message error>{error}</Message><Message>{message}</Message>
    <div className="rounded-2xl border border-line bg-white p-6"><h2 className="text-xl font-bold text-navy">Export your records</h2>
      <p className="mt-2 text-sm text-muted">Download directly owned records as JSON. Passwords, authentication tokens and other candidates are excluded. Private PDFs remain available through the offer download controls.</p>
      <button onClick={() => action(download)} disabled={busy} className={buttonStyle + ' mt-4'}>Download account export</button>
    </div>
    <div className="rounded-2xl border border-line bg-white p-6"><h2 className="text-xl font-bold text-navy">Sign-out controls</h2>
      <p className="mt-2 text-sm text-muted">Normal logout revokes all current sessions on the server. Clearing this browser alone leaves other sessions valid until expiry or a successful server logout.</p>
      <div className="mt-4 flex flex-wrap gap-3"><button className={buttonStyle} disabled={busy} onClick={() => action(() => logout())}>Sign out everywhere</button><button className={secondaryStyle} disabled={busy} onClick={() => logout(true)}>Clear this browser only</button></div>
    </div>
    <form onSubmit={submit} className="space-y-4 rounded-2xl border border-line bg-white p-6"><h2 className="text-xl font-bold text-navy">Request account deletion</h2>
      <p className="text-sm text-muted">A college administrator reviews retention obligations and may close sign-in while erasure is pending. This is a recorded request, not immediate permanent deletion. Review is due within 30 days; retained placement/audit records and backup copies require separate processing.</p>
      <FormField label="Reason for deletion request" required minLength="10" maxLength="1000" value={reason} onChange={e => setReason(e.target.value)} disabled={busy} />
      <FormField label="Type REQUEST DELETION to confirm" required pattern="REQUEST DELETION" value={confirmation} onChange={e => setConfirmation(e.target.value)} disabled={busy} />
      <button className={buttonStyle} disabled={busy}>Submit deletion request</button>
    </form>
    <div className="space-y-3"><h2 className="text-xl font-bold text-navy">Request history</h2>{!rows.length && <p className="text-muted">No deletion requests recorded.</p>}{rows.map(row => <article key={row.id} className="rounded-xl border border-line bg-white p-5"><strong>Request #{row.id} · {row.status.replaceAll('_', ' ')}</strong><p>{row.reason}</p><p className="text-sm text-muted">{row.explanation}</p>{row.review_reason && <p>College review: {row.review_reason}</p>}{row.status === 'requested' && <button className={secondaryStyle + ' mt-3'} disabled={busy} onClick={() => action(async () => { await withdrawDeletion(row.id); setRows(await getDataRequests()) })}>Withdraw request</button>}</article>)}</div>
  </section>
}
