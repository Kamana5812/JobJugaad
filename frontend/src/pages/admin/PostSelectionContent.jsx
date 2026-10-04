import { displayTime } from '../../components/DashboardCard'
import PostSelectionStages from './PostSelectionStages'
import PostSelectionMilestones from './PostSelectionMilestones'
import PostSelectionReasons from './PostSelectionReasons'
import PostSelectionQuality from './PostSelectionQuality'

export default function PostSelectionContent({ data, busy, onPage }) {
  const counts = [['Selected student–drive pairs', data.cohort.selected_pairs], ['Distinct selected students', data.cohort.distinct_students],
    ['Recorded offers', data.cohort.offers], ['Selected pairs without an offer', data.cohort.without_offer]]
  return <div className="space-y-6">
    <div className="rounded-xl border border-line bg-paper p-4">
      <p className="text-sm leading-6 text-navy">{data.scope_explanation}</p>
      <p className="mt-2 text-xs leading-5 text-muted">Included: {data.cohort.recorded_pairs} recorded college pairs and {data.cohort.synthetic_pairs} synthetic/archive pairs. Excluded by the record filter: {data.cohort.excluded_pairs} pairs.</p>
    </div>
    <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{counts.map(([label, count]) => <div key={label}><dt className="text-sm text-muted">{label}</dt><dd className="mt-1 text-2xl font-semibold text-navy">{count}</dd></div>)}</dl>
    {!data.cohort.selected_pairs && <p role="status" className="rounded-xl border border-line p-4 text-sm text-muted">No selected student–drive pairs in this view. No conversion rate is available; choose another record filter or drive.</p>}
    <PostSelectionStages rows={data.stages} />
    <PostSelectionMilestones milestones={data.milestones} closures={data.closures} />
    <PostSelectionReasons data={data} busy={busy} onPage={onPage} />
    <PostSelectionQuality quality={data.data_quality} />
    <div className="border-t border-line pt-4 text-xs leading-6 text-muted"><p>{data.methodology}</p>
      <ul className="mt-2 list-disc space-y-1 pl-5">{data.limitations.map(item => <li key={item}>{item}</li>)}</ul>
      <p className="mt-2">Journey updated {displayTime(data.generated_at)}. Other dashboard totals have their own refresh time.</p>
    </div>
  </div>
}
