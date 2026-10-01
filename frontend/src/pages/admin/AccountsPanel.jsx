import { useCallback, useEffect, useState } from 'react'
import { getAccountQueue, reviewAccount } from '../../api/accounts'
import { errorMessage } from '../../api/student'
import DashboardCard from '../../components/DashboardCard'
import Pagination from '../../components/Pagination'
import { FormField, buttonStyle, secondaryStyle, Message } from '../../components/FormField'
function AccountReview({ item, busy, onReview }) {
  const [reason, setReason] = useState('')
  return <DashboardCard title={item.name} label={`${item.role} · ${item.access_status}`}>
    <p className="text-sm">{item.email} · Email verified: {item.email_verified ? 'yes' : 'no'}</p><p className="mt-2 text-sm">Affiliation reference: {item.affiliation_reference}</p><p className="mt-2 whitespace-pre-wrap text-sm text-muted">{item.context}</p>
    <form className="mt-4 space-y-3" onSubmit={e => { e.preventDefault(); onReview(item, e.nativeEvent.submitter.value, reason) }}>
      <FormField label="Review reason" required minLength="5" maxLength="1000" value={reason} onChange={e => setReason(e.target.value)} disabled={busy} />
      <div className="flex flex-wrap gap-3">{item.access_status !== 'approved' && <button value="approved" className={buttonStyle} disabled={busy}>Approve affiliation</button>}{item.access_status !== 'rejected' && <button value="rejected" className={secondaryStyle} disabled={busy}>Reject / revoke access</button>}</div>
    </form><details className="mt-4 text-sm"><summary className="cursor-pointer text-navy">Review history</summary><ul className="mt-2 space-y-2">{item.history.map(e => <li key={e.id}>{e.action.replaceAll('_', ' ')}: {e.reason}</li>)}</ul></details>
  </DashboardCard>
}
export default function AccountsPanel() {
  const [status, setStatus] = useState('pending'), [offset, setOffset] = useState(0), [data, setData] = useState(null)
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  const refresh = useCallback(async () => { setData(await getAccountQueue(status, offset)) }, [status, offset])
  useEffect(() => { setBusy(true); refresh().catch(e => setError(errorMessage(e))).finally(() => setBusy(false)) }, [refresh])
  async function review(item, decision, reason) { setBusy(true); setError(''); try { await reviewAccount(item.id, { status: decision, version: item.version, reason }); await refresh() } catch(e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  return <section className="space-y-5"><header><h2 className="text-xl font-semibold text-navy">College account approvals</h2><p className="mt-2 text-sm text-muted">Review affiliation through your college’s agreed process. Inbox verification alone does not prove student enrollment or company authority. Decisions require a reason and remain in the audit history. Revoking access takes effect on the next protected request.</p></header>
    <FormField label="Review status" value={status} onChange={e => { setStatus(e.target.value); setOffset(0); setError('') }}>{['pending', 'approved', 'rejected'].map(s => <option key={s} value={s}>{s}</option>)}</FormField>
    <button className={secondaryStyle} disabled={busy} onClick={() => { setBusy(true); refresh().catch(e => setError(errorMessage(e))).finally(() => setBusy(false)) }}>Refresh requests</button><Message error>{error}</Message>
    {data?.total === 0 && <p className="text-sm text-muted">No {status} requests. Applicants must verify their email and submit an affiliation request first.</p>}
    {data?.items.map(item => <AccountReview key={item.id + '-' + item.version} item={item} busy={busy} onReview={review} />)}<Pagination data={data} busy={busy} onPage={setOffset} />
  </section>
}
