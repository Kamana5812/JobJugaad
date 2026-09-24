export default function SkillGapTable({ gaps }) {
  const order = { critical: 0, gap: 1, 'on-track': 2 }
  return <div className="overflow-x-auto rounded-2xl border border-line" tabIndex="0" role="region" aria-label="Skill comparison table">
    <table className="w-full min-w-[620px] text-left text-sm"><caption className="sr-only">Skills compared with the selected drive, critical gaps first</caption>
      <thead className="bg-paper text-xs text-muted"><tr>{['Skill & evidence', 'Recorded /100', 'Target /100', 'Status & next step'].map(label => <th key={label} className="p-4">{label}</th>)}</tr></thead>
      <tbody>{[...gaps].sort((a,b) => order[a.status] - order[b.status] || a.skill_name.localeCompare(b.skill_name)).map(g => <tr key={g.skill_name} className="border-t border-line">
        <th scope="row" className="p-4 font-normal"><span className="font-bold text-navy">{g.skill_name}</span><span className="mt-2 block max-w-sm text-xs leading-5 text-muted">{g.explanation}</span></th>
        <td className="p-4 tabular-nums">{g.proficiency}</td><td className="p-4 tabular-nums">{g.required}</td>
        <td className="p-4"><span className={'inline-block rounded-full px-3 py-1 text-xs font-bold ' + (g.status === 'on-track' ? 'bg-growth-soft text-navy' : g.status === 'critical' ? 'bg-critical-soft text-critical' : 'bg-warning-soft text-navy')}>{g.status === 'on-track' ? 'On track' : g.status === 'critical' ? 'Critical gap' : 'Gap'}</span><p className="mt-2 max-w-sm text-xs leading-5 text-muted">Shortfall: {g.shortfall} points. {g.next_step}</p></td>
      </tr>)}</tbody>
    </table>
  </div>
}
