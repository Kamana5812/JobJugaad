export default function PostSelectionMilestones({ milestones, closures }) {
  return <div className="grid gap-6 lg:grid-cols-2">
    <section aria-label="Independent recorded milestones"><h3 className="font-semibold text-navy">Independent milestone evidence</h3>
      <p className="mt-2 text-sm leading-6 text-muted">These counts do not require the earlier funnel stages. Verification without acceptance is shown explicitly; it is not an accepted offer.</p>
      <dl className="mt-3 divide-y divide-line">{milestones.map(row => <div key={row.key} className="py-3">
        <dt className="flex flex-wrap justify-between gap-2 text-sm font-medium text-navy"><span>{row.label}</span><span>{row.count} pairs · {row.distinct_students} students</span></dt>
        <dd className="mt-1 text-xs leading-5 text-muted">{row.explanation}</dd>
      </div>)}</dl>
    </section>
    <section aria-label="Recorded terminal closures"><h3 className="font-semibold text-navy">Recorded terminal closures</h3>
      <p className="mt-2 text-sm leading-6 text-muted">Each pair has one recorded terminal closure. Conflicting legacy statuses use this precedence: withdrawn → declined → not joined. The same student in different drives can appear in multiple categories; pair totals are not unique-student totals.</p>
      <dl className="mt-3 divide-y divide-line">{closures.map(row => <div key={row.key} className="py-3">
        <dt className="flex flex-wrap justify-between gap-2 text-sm font-medium text-navy"><span>{row.label}</span><span>{row.count} pairs · {row.distinct_students} students</span></dt>
        <dd className="mt-1 text-xs leading-5 text-muted">{row.explanation}<br />{row.missing_reason_count} without a recorded reason.</dd>
      </div>)}</dl>
    </section>
  </div>
}
