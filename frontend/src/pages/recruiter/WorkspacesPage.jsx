import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { getWorkspaces, requestWorkspace, switchWorkspace } from '../../api/workspaces'
import { errorMessage } from '../../api/student'
import { useAuth } from '../../context/AuthContext'
import CollegeSelector from '../../components/CollegeSelector'
import { FormField, Message, buttonStyle, secondaryStyle } from '../../components/FormField'

export default function WorkspacesPage() {
  const { user, authenticate } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [form, setForm] = useState({ college_id: '10219', affiliation_reference: '', context: '', consent: false })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  async function refresh() { setData(await getWorkspaces()) }
  useEffect(() => { let active = true; if (user?.role === 'recruiter') getWorkspaces().then(r => { if (active) setData(r) }).catch(e => { if (active) setError(errorMessage(e)) }); return () => { active = false } }, [user?.college_id, user?.user_id])
  if (!user) return <Navigate to="/auth?role=recruiter&mode=login" replace />
  if (user.role !== 'recruiter') return <Navigate to="/" replace />
  async function action(fn) { setBusy(true); setError(''); setNotice(''); try { await fn() } catch (e) { setError(errorMessage(e)) } finally { setBusy(false) } }
  async function request(event) { event.preventDefault(); await action(async () => { setData(await requestWorkspace({ ...form, college_id: Number(form.college_id) })); setNotice('Request submitted. This college must approve access before you can open its Talent Finder.'); setForm(f => ({ ...f, affiliation_reference: '', context: '', consent: false })) }) }
  async function open(college) { await action(async () => { const result = await switchWorkspace(college); authenticate(result); navigate('/recruiter', { replace: true }) }) }
  return <div className="mx-auto max-w-4xl space-y-6">
    <div><p className="text-sm font-semibold text-saffron-deep">Talent Finder</p><h1 className="mt-2 text-3xl font-bold text-navy">Your college workspaces</h1><p className="mt-3 text-muted">Register once, verify your email once, and request access to each college you recruit from. Sign in with your home college; each campus approves you independently.</p></div>
    <Message error>{error}</Message><Message>{notice}</Message>
    <button className={secondaryStyle} disabled={busy} onClick={() => action(refresh)}>Refresh approvals</button>
    {data && <><p className="text-sm text-muted">{data.explanation}</p><div className="grid gap-4 sm:grid-cols-2">{data.items.map(item => <article key={item.college_id} className="rounded-2xl border border-line bg-white p-6"><h2 className="text-xl font-bold text-navy">{item.college_name}</h2><p className="mt-2 text-sm text-muted">{item.is_home ? 'Home college · use at login and password recovery' : 'Additional college'}{item.active ? ' · current workspace' : ''}</p><p className="mt-3 font-semibold">Access: {item.access_status}</p><button className={buttonStyle + ' mt-4'} disabled={busy || (!item.is_home && item.access_status !== 'approved')} onClick={() => open(item.college_id)}>{item.is_home && item.access_status !== 'approved' ? 'Open home verification & approval' : 'Open Talent Finder →'}</button></article>)}</div></>}
    <form onSubmit={request} className="space-y-5 rounded-2xl border border-line bg-white p-6 sm:p-8"><h2 className="text-2xl font-bold text-navy">Request a college workspace</h2><p className="text-sm text-muted">Verify your home email first. Company name and industry are copied from your home profile; campus profiles and drives remain separate. Existing accounts are never merged by email.</p>
      <CollegeSelector label="College to recruit from" hint="This college reviews your request; your home login college stays the same." value={form.college_id} disabled={busy} onChange={e => setForm({ ...form, college_id: e.target.value })} />
      <FormField label="Company affiliation reference" required minLength="3" maxLength="120" value={form.affiliation_reference} disabled={busy} onChange={e => setForm({ ...form, affiliation_reference: e.target.value })} />
      <FormField label="Supporting context (optional)" maxLength="1000" value={form.context} disabled={busy} onChange={e => setForm({ ...form, context: e.target.value })} />
      <label className="flex gap-3 text-sm"><input type="checkbox" required checked={form.consent} disabled={busy} onChange={e => setForm({ ...form, consent: e.target.checked })} />I agree to share my account and company affiliation with this college for review.</label>
      <button className={buttonStyle} disabled={busy}>{busy ? 'Saving…' : 'Submit for college approval'}</button>
    </form><Link className="text-sm font-semibold text-navy underline" to="/account">Account, privacy and sign-out controls</Link>
  </div>
}
