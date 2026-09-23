import DashboardCard, { displayTime } from '../../components/DashboardCard'
import ConversionChart from '../../components/ConversionChart'
export default function AnalyticsPanel({ data }) {
  const tiles = [['Students', data.students], ['Placement %', data.placement_percent === null ? '—' : data.placement_percent + '%'],
    ['Recruiters', data.recruiters], ['Drives', data.drives]]
  const amount = value => value === null ? 'Not available' : value.toFixed(2) + ' LPA'
  return <div className="space-y-6">
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{tiles.map(([label, value]) => <DashboardCard key={label} label={label}>
      <p className="mt-3 text-4xl font-bold text-navy">{value}</p>
      {label === 'Placement %' && <p className="mt-2 text-xs text-muted">Accepted-offer proxy</p>}
    </DashboardCard>)}</div>
    <p className="text-sm text-muted">{data.placement_explanation}</p>
    <div className="grid min-w-0 gap-6 lg:grid-cols-2"><ConversionChart title="01 Branch overview" rows={data.branch_conversion} />
      <ConversionChart title="02 Skill overview" rows={data.skill_conversion} /></div>
    <DashboardCard title="03 Advertised packages" label="Drive CTC · not accepted offers">
      <dl className="grid gap-5 sm:grid-cols-3">{[['Minimum', data.ctc_min_lpa], ['Mean', data.ctc_mean_lpa], ['Maximum', data.ctc_max_lpa]].map(([label, value]) =>
        <div key={label}><dt className="text-sm text-muted">{label}</dt><dd className="text-2xl font-bold text-navy">{amount(value)}</dd></div>)}</dl>
    </DashboardCard>
    <DashboardCard title="04 Recorded offer outcomes" label="Synthetic demonstration records included">
      <dl className="grid gap-5 sm:grid-cols-3">{[['Students with accepted offers', data.accepted_students], ['Students recorded joined', data.joined_students], ['Offers (all stages)', data.offer_count]].map(([label, value]) => <div key={label}><dt className="text-sm text-muted">{label}</dt><dd className="text-2xl font-bold text-navy">{value}</dd></div>)}</dl>
      <p className="mt-4 text-sm text-muted">{data.synthetic_offer_count} offers are synthetic. Accepted offers and joining are distinct stages.</p>
      <h3 className="mb-3 mt-6 font-bold text-navy">CTC for active accepted offers</h3>
      <dl className="grid gap-5 sm:grid-cols-3">{[['Minimum', data.accepted_ctc_min_lpa], ['Mean', data.accepted_ctc_mean_lpa], ['Maximum', data.accepted_ctc_max_lpa]].map(([label, value]) => <div key={label}><dt className="text-sm text-muted">{label}</dt><dd className="text-2xl font-bold text-navy">{amount(value)}</dd></div>)}</dl>
    </DashboardCard>
    <p className="text-xs leading-6 text-muted">{data.methodology}<br />Updated {displayTime(data.generated_at)}.</p>
  </div>
}
