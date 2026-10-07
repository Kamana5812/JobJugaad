import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getAccess, requestVerification, requestAccess } from '../api/accounts'
import { errorMessage } from '../api/student'
import { FormField, buttonStyle, secondaryStyle, Message } from './FormField'
import DashboardCard from './DashboardCard'

export default function AccountOnboarding() {
  const { user, refreshUser, logout } = useAuth()
  const [data, setData] = useState(null)
  const [form, setForm] = useState({ affiliation_reference: '', context: '', consent: false })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  async function refresh() { const next = await getAccess(); setData(next); await refreshUser() }
  useEffect(() => { getAccess().then(setData).catch(e => setError(errorMessage(e))) }, [])
  async function perform(action, success = 'College access request saved.') {
    setBusy(true); setError(''); setNotice('')
    try { const result = await action(); setNotice(result?.detail || success); await refresh() }
    catch (e) { setError(errorMessage(e)) } finally { setBusy(false) }
  }
  return <div className="mx-auto max-w-2xl space-y-6">
    <header><p className="text-sm text-muted">{user.college_name}</p><h1 className="mt-2 text-3xl font-semibold text-navy">Activate your college workspace</h1><p className="mt-3 text-sm text-muted">{user.email} · {user.role}. Inbox verification and college approval are separate checks.</p></header>
    <Message error>{error}</Message><Message>{notice}</Message>
    {user.role === 'recruiter' && !user.is_demo && <Link className={secondaryStyle} to="/recruiter/workspaces">Your college workspaces →</Link>}
    <DashboardCard title="01 Verify your email" label={data?.email_verified ? 'Verified' : 'Verification required'}>
      <p className="text-sm text-muted">Open the verification link in your email, then return here and refresh your account.</p>
      {!data?.email_verified && <button className={buttonStyle + ' mt-4'} disabled={busy || !data?.email_delivery_ready} onClick={() => perform(requestVerification)}>Send verification email</button>}
      {data && !data.email_delivery_ready && !data.email_verified && <p className="mt-3 text-sm text-muted">Email delivery is awaiting server configuration. Your account is saved; access stays restricted.</p>}
    </DashboardCard>
    {user.role !== 'admin' && <DashboardCard title="02 Request college approval" label={data?.access_status || 'Loading'}>
      <p className="text-sm text-muted">Your placement administrator reviews your affiliation. Student: enter your enrollment reference. Recruiter: enter your company affiliation reference. Exchange supporting documents through your college’s agreed channel; do not paste passwords or private documents here.</p>
      {data?.email_verified && (!data.requested_at || data.access_status === 'rejected') && <form className="mt-4 space-y-4" onSubmit={e => { e.preventDefault(); perform(() => requestAccess(form)) }}>
        <FormField label="Affiliation reference" required minLength="3" maxLength="120" value={form.affiliation_reference} onChange={e => setForm({ ...form, affiliation_reference: e.target.value })} />
        <FormField label="Supporting context (optional)" maxLength="1000" value={form.context} onChange={e => setForm({ ...form, context: e.target.value })} />
        <label className="flex gap-3 text-sm"><input type="checkbox" required checked={form.consent} onChange={e => setForm({ ...form, consent: e.target.checked })} />I agree to share this request with my college administrator for affiliation review.</label>
        <button className={buttonStyle} disabled={busy}>Submit for review</button>
      </form>}
      {data?.requested_at && data.access_status === 'pending' && <p className="mt-4 text-sm">Request received. Waiting for your college administrator’s decision.</p>}
      {data?.history?.length > 0 && <ul className="mt-4 space-y-2 text-sm">{data.history.map(event => <li key={event.id}><strong>{event.action.replaceAll('_', ' ')}:</strong> {event.reason}</li>)}</ul>}
    </DashboardCard>}
    <div className="flex gap-3"><button className={secondaryStyle} disabled={busy} onClick={() => perform(async () => {}, 'Account refreshed.')}>Refresh account</button><button className={secondaryStyle} onClick={logout}>Sign out</button></div>
  </div>
}
