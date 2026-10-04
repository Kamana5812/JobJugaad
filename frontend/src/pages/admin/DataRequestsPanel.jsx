import { useEffect, useState } from 'react'
import { getDeletionQueue, reviewDeletion } from '../../api/accountData'
import { errorMessage } from '../../api/student'
import { FormField, Message, secondaryStyle } from '../../components/FormField'
export default function DataRequestsPanel() {
  const [rows, setRows] = useState([])
  const [reason, setReason] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function load() { setError(''); try { setRows(await getDeletionQueue()) } catch (e) { setError(errorMessage(e)) } }
  useEffect(() => { load() }, [])
  async function review(row, action) {
    setBusy(true); setError('')
    try { await reviewDeletion(row.id, { action, reason: reason[row.id] || '' }); await load() }
    catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  return <section className="space-y-4"><h2 className="text-2xl font-bold text-navy">Account deletion review</h2><p className="text-sm text-muted">Restriction revokes access but retains placement records for erasure review. It is not a completed deletion. Administrator accounts require owner-managed succession. Review retained-record needs within 30 days; do not claim erasure before processing files, history and backups.</p><button className={secondaryStyle} onClick={load} disabled={busy}>Refresh requests</button><Message error>{error}</Message>{!rows.length && <p>No requests recorded.</p>}{rows.map(row => <article key={row.id} className="space-y-3 rounded-xl border border-line bg-white p-5"><h3 className="font-bold text-navy">Request #{row.id} · Account #{row.user_id} · {row.status.replaceAll('_', ' ')}</h3><p>{row.reason}</p>{row.review_reason && <p>Review: {row.review_reason}</p>}{row.retention_until && <p>Erasure review due: {new Date(row.retention_until).toLocaleDateString()}</p>}{row.status === 'requested' && <><FormField label={`Review reason for request ${row.id}`} minLength="10" maxLength="1000" value={reason[row.id] || ''} onChange={e => setReason({ ...reason, [row.id]: e.target.value })} disabled={busy} /><div className="flex flex-wrap gap-3"><button className={secondaryStyle} disabled={busy || (reason[row.id] || '').trim().length < 10} onClick={() => review(row, 'restrict')}>Restrict access · erasure pending</button><button className={secondaryStyle} disabled={busy || (reason[row.id] || '').trim().length < 10} onClick={() => review(row, 'reject')}>Record rejection with reason</button></div></>}</article>)}</section>
}
