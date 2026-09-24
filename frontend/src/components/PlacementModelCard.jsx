const signed = (value) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}`
export default function PlacementModelCard({ signal, evaluation, dirty, datasetName = 'Campus Recruitment', splitDescription = 'One fixed stratified split.' }) {
  return <div className="space-y-5">
    {dirty && <p role="status" className="rounded-xl bg-warning-soft p-3 text-sm text-navy">Unsaved academic changes. The result below uses only your last saved inputs.</p>}
    {signal.available && <p className="text-4xl font-bold text-navy">{signal.score.toFixed(2)}<span className="text-base font-medium text-muted"> / 100 · uncalibrated model score</span></p>}
    {!signal.available && <p className="font-semibold text-navy">Model score not available</p>}
    <p className="leading-7 text-navy">{signal.explanation}</p>
    {signal.available && <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full min-w-[480px] text-left text-sm">
        <caption className="p-4 text-left font-bold text-navy">Why this result? Your model factors.</caption>
        <thead className="bg-paper text-muted"><tr><th className="p-3">Recorded input</th><th className="p-3">Value</th><th className="p-3 text-right">Change in points</th></tr></thead>
        <tbody><tr className="border-t border-line"><th className="p-3 font-medium">Training-root baseline</th><td className="p-3">All trees, averaged</td><td className="p-3 text-right">{signal.baseline.toFixed(2)}</td></tr>
          {signal.breakdown.map((factor) => <tr key={factor.key} className="border-t border-line"><th scope="row" className="p-3 font-medium text-navy">{factor.label}</th><td className="p-3">{factor.value}</td><td className="p-3 text-right font-semibold text-navy">{signed(factor.contribution)}</td></tr>)}
        </tbody>
        <tfoot className="border-t border-line bg-paper"><tr><th colSpan="2" className="p-3">Baseline + contributions = model score</th><td className="p-3 text-right font-bold">{signal.score.toFixed(2)}</td></tr></tfoot>
      </table>
      <p className="border-t border-line p-3 text-xs text-muted">Displayed values are rounded. Contributions describe how this model reached its result, not what causes placement.</p>
    </div>}
    <p className="text-sm leading-6 text-muted">{signal.methodology}</p>
    <ul className="list-disc space-y-2 pl-5 text-xs leading-5 text-muted">{signal.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
    {evaluation && <details className="rounded-xl border border-line p-4">
      <summary className="cursor-pointer font-semibold text-navy">Measured evaluation on public data</summary>
      <p className="mt-3 text-sm leading-6 text-muted">{datasetName}: {evaluation.dataset_rows} public labeled records, {evaluation.train_rows} used for training and {evaluation.test_rows} held out for testing. {splitDescription} These results apply to this test sample, not a guarantee for your college.</p>
      {evaluation.distinct_profiles != null && <p className="mt-2 text-sm leading-6 text-muted">Only {evaluation.distinct_profiles} distinct modeled profiles: {evaluation.train_groups} training groups and {evaluation.test_groups} test groups. Repeated rows are not independent profiles. Always predicting the training majority class scored {(evaluation.baseline_accuracy * 100).toFixed(2)}% on this test set.</p>}
      <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">{[['accuracy','Accuracy'],['precision','Placed precision'],['recall','Placed recall'],['f1','Placed F1']].map(([key,label]) => <div key={key}><dt className="text-muted">{label}</dt><dd className="font-bold text-navy">{(evaluation[key] * 100).toFixed(2)}%</dd></div>)}</dl>
      <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><caption className="pb-2 text-left font-semibold">Confusion matrix · rows actual, columns predicted</caption><thead><tr><th className="p-2">Actual outcome</th><th className="p-2">Not Placed</th><th className="p-2">Placed</th></tr></thead><tbody>{['Not Placed','Placed'].map((label,index) => <tr key={label} className="border-t border-line"><th className="p-2 font-medium">{label}</th>{evaluation.confusion_matrix[index].map((count,column) => <td key={column} className="p-2">{count}</td>)}</tr>)}</tbody></table></div>
      <a href={evaluation.source_url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-sm font-semibold text-navy underline">View public dataset source</a>
    </details>}
  </div>
}
