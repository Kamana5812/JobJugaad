import assert from 'node:assert/strict'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const server = await createServer({ root: fileURLToPath(new URL('../', import.meta.url)), server: { middlewareMode: true, hmr: false }, appType: 'custom' })
try {
  const component = async path => (await server.ssrLoadModule(path)).default
  const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props))
  const Experience = await component('/src/components/ExperienceEditor.jsx')
  const experience = render(Experience, { items: [{ kind: 'internship', organization: '<script>work</script>', role: 'Intern', description: 'Built a test API', reference: null }], onChange() {} })
  assert.match(experience, /do not change the weighted readiness/)
  assert.match(experience, /&lt;script&gt;work&lt;\/script&gt;/)
  assert.doesNotMatch(experience, /<script>/)
  const Evidence = await component('/src/components/TextEvidence.jsx')
  const text = render(Evidence, { evidence: { score: 20, factor_breakdown: [{ term: '<img src=x>', contribution: 20 }], explanation: 'Lexical wording only; no eligibility change.', methodology: 'Pair-fitted TF-IDF; no calibrated confidence.' } })
  assert.match(text, /20\/100/)
  assert.match(text, /20 points/)
  assert.match(text, /no eligibility change/)
  assert.match(text, /&lt;img src=x&gt;/)
  assert.doesNotMatch(text, /<img/)
  const State = await component('/src/components/DriveState.jsx')
  const state = render(State, { job: { id: 1, title: 'Controlled closed drive', is_open: false, version: 2, description: 'Historical requirements', lifecycle_events: [{ actor_role: 'admin', actor_user_id: 7, is_open: false, reason: '<script>reason</script>', created_at: '2026-10-05T10:00:00Z' }] }, onSaved() {} })
  assert.match(state, /Reopen drive/)
  assert.match(state, /Existing evidence, applications, interviews and offers remain/)
  assert.match(state, /&lt;script&gt;reason&lt;\/script&gt;/)
  const Records = await component('/src/components/AssessmentRecords.jsx')
  const row = { id: 1, student_id: 2, title: 'Reviewed result', student_name: 'Controlled student', kind: 'aptitude', score: 30, maximum: 40, use_for_scoring: true, explanation: '30 / 40 × 100 = 75; staff declaration.', source: 'Controlled provider', reference: 'Controlled reference', recorded_by: 7, reason: 'Reviewed original result', created_at: '2026-10-05T10:00:00Z', assessed_on: '2026-10-04T10:00:00Z' }
  assert.match(render(Records, { items: [row] }), /Adopted: latest active result/)
  assert.match(render(Records, { items: [{ ...row, use_for_scoring: false }] }), /Evidence only: not used/)
  const Interviews = await component('/src/pages/admin/InterviewList.jsx')
  const booking = { id: 1, student_id: 2, job_id: 3, status: 'scheduled', event_type: 'assessment', round_number: 1, round_name: 'Aptitude test', venue: 'Room', panel_id: 'Panel', scheduled_time: '2026-10-06T10:00:00Z', end_time: '2026-10-06T10:30:00Z' }
  const calendar = render(Interviews, { items: [booking], names: { student: () => 'Controlled student', job: () => 'Controlled drive' }, perform() {} })
  assert.match(calendar, /Assessment event/)
  assert.doesNotMatch(calendar, /option value="selected"/)
  assert.match(calendar, /cannot grant selection or an offer/)
  console.log('PASS completion interface checks: bounded experience form, escaped evidence, reconciled lexical score, audited closure, adoption labels and assessment-event outcome guard. SSR only; no live browser claim.')
} finally { await server.close() }
