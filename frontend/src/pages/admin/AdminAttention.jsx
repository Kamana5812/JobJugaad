import { secondaryStyle } from '../../components/FormField'
export default function AdminAttention({ board, onSection }) {
  const pending = board.proposals.filter(item => item.status === 'pending')
  return <section className="grid gap-4 lg:grid-cols-2" aria-label="Items for human review">
    <div className="rounded-2xl border border-line bg-white p-6"><p className="text-xs font-bold uppercase tracking-widest text-saffron-deep">Scheduling review</p><h2 className="mt-3 text-xl font-bold text-navy">{board.conflicts.length} recorded conflict{board.conflicts.length === 1 ? '' : 's'}</h2>
      {board.conflicts.length ? <ul className="mt-4 space-y-3 text-sm text-muted">{board.conflicts.slice(0, 3).map((item, index) => <li key={index} className="rounded-xl bg-warning-soft p-3">{item.explanation}</li>)}</ul> : <p className="mt-3 text-sm text-muted">No overlaps found in the recorded calendar.</p>}
      <p className="mt-4 text-xs leading-5 text-muted">{pending.length} proposal{pending.length === 1 ? '' : 's'} awaiting approval. Proposed slots are not reserved until an administrator approves them.</p><button className={secondaryStyle + ' mt-4'} onClick={() => onSection('scheduling')}>Review scheduling →</button>
    </div>
    <div className="rounded-2xl border border-line bg-growth-soft p-6"><p className="text-xs font-bold uppercase tracking-widest text-navy">Placement support</p><h2 className="mt-3 text-xl font-bold text-navy">A little support. A clearer next step.</h2><p className="mt-4 text-sm leading-7 text-navy/80">Review named indicators and recommended interventions alongside each student’s circumstances. The rule flags a need for review; it does not predict failure.</p><button className={secondaryStyle + ' mt-5'} onClick={() => onSection('support')}>Review support evidence →</button></div>
  </section>
}
