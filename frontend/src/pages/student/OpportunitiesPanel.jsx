import { useEffect, useState } from 'react'
import { getOpportunities, errorMessage } from '../../api/student'
import { FormField, Message, secondaryStyle } from '../../components/FormField'
import Pagination from '../../components/Pagination'
import OpportunityCard from './OpportunityCard'
import SkillGapTable from './SkillGapTable'

export function OpportunitiesContent({ data, status, dirty, onStatus, onTarget, onPage }) {
  return <div className="space-y-8">
    <section id="skill-gaps" className="scroll-mt-6 rounded-3xl border border-line bg-white p-6 sm:p-8">
      <h2 className="text-2xl font-bold text-navy"><span className="mr-3 text-saffron-deep">02</span>Kahan Kami Hai?</h2><p className="mt-3 text-sm leading-6 text-muted">Compare your saved skill evidence with a specific drive. Critical gaps appear first; missing evidence is not a judgment of your ability.</p>
      {data.roles.length ? <><div className="my-6 max-w-2xl"><FormField label="Choose a target drive" value={data.target?.job_id || ''} onChange={event => onTarget(Number(event.target.value))}>{data.roles.map(role => <option key={role.job_id} value={role.job_id}>{role.title} · {role.company_name} (#{role.job_id})</option>)}</FormField></div><SkillGapTable gaps={data.target?.skill_gaps || []} />
        <p className="mt-4 text-xs leading-5 text-muted">Proposed thresholds: on track at or above the target; gap from half the target; critical below half. Inputs are self-reported. These labels do not make a hiring decision.</p></> : <p className="mt-5 rounded-xl bg-paper p-5 text-sm text-muted">No drives have been recorded in your college yet. Add your profile evidence while your placement team prepares opportunities.</p>}
    </section>
    <section id="opportunities" className="scroll-mt-6 space-y-5"><div><h2 className="text-2xl font-bold text-navy"><span className="mr-3 text-saffron-deep">03</span>Aapke Liye Sahi Jobs</h2><p className="mt-3 text-sm leading-6 text-muted">{data.explanation}</p></div>
      {dirty && <Message>Unsaved profile changes are not included. Save your profile to refresh these comparisons.</Message>}
      <div className="flex flex-wrap items-end justify-between gap-4 rounded-2xl border border-line bg-white p-5"><FormField label="Opportunity view" value={status} onChange={event => onStatus(event.target.value)}><option value="eligible">Meets calculated eligibility ({data.eligible_count})</option><option value="excluded">Gaps / excluded roles ({data.excluded_count})</option><option value="all">All college drives</option></FormField><p className="text-xs text-muted">Descending match score · ties by drive ID</p></div>
      {!data.items.length && <p className="rounded-2xl border border-dashed border-line bg-white p-6 text-sm text-muted">{data.roles.length ? status === 'eligible' ? 'No roles meet all current rules. Choose “Gaps / excluded roles” to see what to work on.' : 'No drives in this view. Try another view or return to the first page.' : 'Your college has no recorded drives yet.'}</p>}
      {data.items.map((opportunity, index) => <OpportunityCard key={opportunity.job_id} opportunity={opportunity} position={data.offset + index + 1} />)}
      <Pagination data={data} busy={false} onPage={onPage} /><p className="text-xs text-muted">Calculated from saved evidence: {new Date(data.calculated_at).toLocaleString()}.</p>
    </section>
  </div>
}
export default function OpportunitiesPanel({ studentId, revision, dirty, onExpired }) {
  const [status, setStatus] = useState('eligible')
  const [offset, setOffset] = useState(0)
  const [targetId, setTargetId] = useState(null)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    getOpportunities(studentId, { status, offset, limit: 3, target_job_id: targetId || undefined }).then(value => { if (active) setData(value) })
      .catch(failure => { if (active) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) } })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [studentId, revision, status, offset, targetId, retry])
  if (loading) return <section id="skill-gaps" className="rounded-3xl border border-line bg-white p-8"><p role="status">Comparing your saved profile with college drives…</p></section>
  if (error) return <section id="skill-gaps" className="space-y-4 rounded-3xl border border-line bg-white p-8"><h2 className="font-bold text-navy">Skill gaps & opportunities</h2><Message error>{error}</Message><button onClick={() => { setTargetId(null); setOffset(0); setRetry(v => v + 1) }} className={secondaryStyle}>Retry comparisons</button></section>
  return data && <OpportunitiesContent data={data} status={status} dirty={dirty} onStatus={value => { setStatus(value); setOffset(0) }} onTarget={setTargetId} onPage={setOffset} />
}
