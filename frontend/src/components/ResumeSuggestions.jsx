import { useEffect, useState } from 'react'
import { getResumeSuggestions } from '../api/nlp'
import { errorMessage } from '../api/student'
import { Message, secondaryStyle, buttonStyle } from './FormField'

export default function ResumeSuggestions({ profile, disabled, onSuggested, onExpired }) {
  const [data, setData] = useState(null)
  const [selected, setSelected] = useState({})
  const [proficiency, setProficiency] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  useEffect(() => { setData(null); setSelected({}); setProficiency({}); setNotice('') }, [profile.id, profile.resume_text])
  async function preview() {
    setBusy(true); setError(''); setNotice(''); setData(null); setSelected({})
    try { setData(await getResumeSuggestions(profile.id)) }
    catch (failure) { if (failure.response?.status === 401) onExpired(); else setError(errorMessage(failure)) }
    finally { setBusy(false) }
  }
  const choices = data?.suggestions.map((item, index) => ({ ...item, index })).filter(item => selected[item.index]) || []
  const invalid = choices.some(item => item.field === 'skill' && (proficiency[item.index] === undefined || proficiency[item.index] === '' || Number(proficiency[item.index]) < 0 || Number(proficiency[item.index]) > 100))
  function apply() {
    onSuggested(choices.map(item => ({ ...item, proficiency: item.field === 'skill' ? Number(proficiency[item.index]) : undefined })))
    setSelected({}); setNotice('Suggestions copied into your unsaved profile editor. Review it and click Save profile & recalculate to persist changes.')
  }
  return <section className="space-y-4 rounded-xl border border-line bg-white p-6">
    <h3 className="font-bold text-navy">Review resume field suggestions</h3><p className="text-sm text-muted">Local pattern extraction, with source text for review. Nothing is selected or saved automatically. Skill mentions do not establish proficiency.</p>
    <button className={secondaryStyle} disabled={busy || disabled || !profile.resume_text} onClick={preview}>{busy ? 'Finding suggestions…' : 'Preview extracted fields'}</button>
    <Message error>{error}</Message><Message>{notice}</Message>
    {data && <><p className="text-sm">{data.explanation}</p><p className="text-xs text-muted">{data.methodology}</p>{!data.suggestions.length && <p>No unambiguous fields found. Enter evidence manually.</p>}
      {data.suggestions.map((item, i) => <div key={i} className="space-y-2 rounded-xl bg-paper p-4"><label className="flex gap-3 text-sm"><input type="checkbox" checked={!!selected[i]} disabled={disabled} onChange={e => setSelected({ ...selected, [i]: e.target.checked })} /><span><strong>{item.field}: {item.value}</strong></span></label><p className="whitespace-pre-wrap text-xs text-muted">Source: {item.source}</p>
        {item.field === 'skill' && <label className="block text-sm">Your proficiency /100<input className="ml-3 w-24 rounded-lg border border-line p-2" type="number" min="0" max="100" step="1" value={proficiency[i] ?? ''} disabled={disabled} onChange={e => setProficiency({ ...proficiency, [i]: e.target.value })} /></label>}</div>)}
      <button className={buttonStyle} disabled={disabled || !choices.length || invalid} onClick={apply}>Copy selected suggestions to profile editor</button>{invalid && <p className="text-sm text-muted">Enter a proficiency from 0 to 100 for each selected skill.</p>}</>}
  </section>
}
