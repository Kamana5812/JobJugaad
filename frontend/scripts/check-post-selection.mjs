import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const root = fileURLToPath(new URL('../', import.meta.url))
const server = await createServer({ root, server: { middlewareMode: true, hmr: false }, appType: 'custom' })
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props))
const stages = [
  { key: 'selected', label: 'Selected', count: 5, distinct_students: 4, previous_count: null, conversion_percent: null, not_reached_from_previous: 0, pending_from_previous: 0, closed_from_previous: 0, explanation: 'Five distinct student–drive pairs have recorded selection evidence.' },
  { key: 'issued', label: 'Issued', count: 4, distinct_students: 3, previous_count: 5, conversion_percent: 80, not_reached_from_previous: 1, pending_from_previous: 1, closed_from_previous: 0, explanation: 'Four selected pairs have recorded issuance evidence.' },
  { key: 'accepted', label: 'Accepted', count: 3, distinct_students: 2, previous_count: 4, conversion_percent: 75, not_reached_from_previous: 1, pending_from_previous: 0, closed_from_previous: 1, explanation: 'Three issued pairs have recorded acceptance evidence.' },
  { key: 'verified', label: 'Accepted and verified', count: 2, distinct_students: 2, previous_count: 3, conversion_percent: 66.67, not_reached_from_previous: 1, pending_from_previous: 1, closed_from_previous: 0, explanation: 'Two accepted pairs also have recorded verification evidence.' },
  { key: 'joined', label: 'Joined', count: 1, distinct_students: 1, previous_count: 2, conversion_percent: 50, not_reached_from_previous: 1, pending_from_previous: 0, closed_from_previous: 1, explanation: 'One pair has all earlier milestones and recorded joining.' },
]
const milestones = [{ key: 'verified_without_acceptance', label: 'Verification recorded without acceptance', count: 1, distinct_students: 1, explanation: 'Verification is recorded, with no acceptance evidence; timing order is not inferred.' }]
const closures = [{ key: 'withdrawn', label: 'Withdrawn', count: 1, distinct_students: 1, missing_reason_count: 0, explanation: 'One offer currently records withdrawal.' }, { key: 'not_joined', label: 'Not joined', count: 1, distinct_students: 1, missing_reason_count: 1, explanation: 'One offer currently records non-joining.' }]
const reasons = [
  { closure: 'withdrawn', reason: '<script>Not markup</script>\nPersonal recorded context.', reason_source: 'recorded_action', count: 1, synthetic_count: 0, recorded_count: 1 },
  { closure: 'declined', reason: 'Fictional imported workflow note.', reason_source: 'synthetic_import', count: 1, synthetic_count: 1, recorded_count: 0 },
  { closure: 'not_joined', reason: null, reason_source: 'missing', count: 1, synthetic_count: 0, recorded_count: 1 },
]
const data = { scope: 'all', scope_explanation: 'This view combines recorded college workflow with explicitly labeled synthetic/archive records; employment is not independently verified.',
  cohort: { selected_pairs: 5, distinct_students: 4, offers: 4, without_offer: 1, synthetic_pairs: 2, recorded_pairs: 3, excluded_pairs: 1 }, stages, milestones, closures, reasons, reason_total: 24, offset: 0, limit: 20,
  data_quality: { offers_without_history: 0, invalid_offer_history_events: 1, invalid_selection_history_events: 0, withdrawn_without_issuance_evidence: 0, accepted_without_issuance_evidence: 0, selection_from_linked_offer: 4, selection_from_history: 1, offers_with_mismatched_interview: 0, historical_selection_no_current_selection: 1 },
  methodology: 'Recorded historical milestones are counted once per student–drive pair, with explicit previous-stage denominators.', limitations: ['Recorded progress does not establish timing order.', 'Synthetic records are fictional outcomes.'], generated_at: '2026-10-04T09:00:00Z' }
let passed = 0
const check = (name, run) => { run(); passed++; console.log('PASS ' + name) }
try {
  const Content = (await server.ssrLoadModule('/src/pages/admin/PostSelectionContent.jsx')).default
  const Panel = (await server.ssrLoadModule('/src/pages/admin/PostSelectionPanel.jsx')).default
  const StageTable = (await server.ssrLoadModule('/src/pages/admin/PostSelectionStages.jsx')).default
  const ReasonTable = (await server.ssrLoadModule('/src/pages/admin/PostSelectionReasons.jsx')).default
  const props = { data, busy: false, onPage: () => {} }, html = render(Content, props)
  check('pair and student units remain distinct with record scope and exclusions', () => {
    assert(html.includes('Selected student–drive pairs') && html.includes('Distinct selected students'))
    assert(html.includes(data.scope_explanation) && html.includes('3 recorded college pairs and 2 synthetic/archive pairs'))
    assert(html.includes('Excluded by the record filter: 1 pairs'))
  })
  check('nested milestones preserve every denominator, explanation and recorded closure distinction', () => {
    for (const row of stages) assert(html.includes(row.explanation))
    for (const value of ['4 / 5', '3 / 4', '2 / 3', '1 / 2', '66.67% of previous-stage pairs', 'Cohort baseline', '1 without a recorded offer closure', '1 with a recorded offer closure']) assert(html.includes(value))
    assert(html.includes('No recorded closure does not mean active progress or a dropout') && html.includes('Acceptance and verification can happen in either order'))
  })
  check('independent verification and terminal closures do not infer sequence or merge outcomes', () => {
    assert(html.includes('Verification recorded without acceptance') && html.includes(milestones[0].explanation))
    for (const row of closures) assert(html.includes(row.explanation))
    assert(html.includes('Each pair has one recorded terminal closure') && html.includes('withdrawn → declined → not joined'))
    assert(html.includes('same student in different drives can appear in multiple categories'))
    assert(!html.includes('verification before acceptance') && !html.includes('predicted dropout'))
  })
  check('literal reasons are escaped with explicit import and missing provenance', () => {
    assert(html.includes('&lt;script&gt;Not markup&lt;/script&gt;') && !html.includes('<script>'))
    assert(html.includes('whitespace-pre-wrap') && html.includes('Synthetic import note') && html.includes('No audited reason recorded') && html.includes('Recorded action reason'))
    assert(html.includes('not an inferred cause or automated classification'))
  })
  check('reason groups page independently with correct total and busy gates', () => {
    const paging = render(ReasonTable, props)
    assert(paging.includes('1–20 of 24') && paging.match(/<button[^>]*disabled=""/))
    const locked = render(ReasonTable, { ...props, busy: true })
    assert.equal((locked.match(/<button[^>]*disabled=""/g) || []).length, 2)
    assert(render(ReasonTable, { ...props, data: { ...data, reasons: [], reason_total: 0 } }).includes('No terminal closure reasons'))
  })
  check('zero denominators and empty cohorts show unavailable rates, never fabricated zero conversions', () => {
    const emptyStages = stages.map(row => ({ ...row, count: 0, distinct_students: 0, previous_count: row.key === 'selected' ? null : 0, conversion_percent: null, not_reached_from_previous: 0, pending_from_previous: 0, closed_from_previous: 0 }))
    const empty = render(Content, { ...props, data: { ...data, cohort: { ...data.cohort, selected_pairs: 0 }, stages: emptyStages } })
    assert(empty.includes('No selected student–drive pairs') && empty.includes('No conversion rate is available'))
    assert(empty.includes('Rate unavailable: no previous-stage pairs') && !empty.includes('0% of previous-stage pairs') && !empty.includes('null%'))
    assert(!render(StageTable, { rows: emptyStages }).includes('role="img"'))
  })
  check('coverage warnings, methodology and limitations stay visible with refresh time', () => {
    assert(html.includes('Offer events with incomplete or invalid stage snapshots') && html.includes('Evidence sources may overlap'))
    assert(html.includes(data.methodology) && html.includes(data.limitations[1]) && html.includes('Other dashboard totals have their own refresh time'))
  })
  check('initial panel defaults to recorded workflow and has explicit loading/filter/refresh controls', () => {
    const panel = render(Panel, { refreshKey: data.generated_at })
    assert(panel.includes('value="recorded" selected=""') && panel.includes('Journey records') && panel.includes('Journey drive'))
    assert(panel.includes('Loading the selected workflow records') && panel.includes('Refresh journey and reasons'))
    assert(panel.includes('interview rounds do not add extra pairs') && panel.includes('not independently verified employment or predictions'))
  })
  const api = (await server.ssrLoadModule('/src/api/client.js')).api
  const analytics = await server.ssrLoadModule('/src/api/postSelection.js'), requests = []
  api.defaults.headers.common.Authorization = 'Bearer local-analytics-transport-fixture'
  api.defaults.adapter = async config => { requests.push(config); return { data, status: 200, statusText: 'OK', headers: {}, config } }
  await analytics.getPostSelection()
  await analytics.getPostSelection({ scope: 'synthetic', job_id: '18', offset: 20 })
  await analytics.getPostSelection({ scope: 'all', job_id: '', offset: 0 })
  check('authenticated read-only requests transmit source, optional drive and reason paging exactly', () => {
    for (const request of requests) { assert.equal(request.method, 'get'); assert.equal(request.url, '/admin/analytics/post-selection'); assert.equal(request.headers.get('Authorization'), 'Bearer local-analytics-transport-fixture'); assert.equal(request.data, undefined) }
    assert.deepEqual(requests[0].params, { scope: 'recorded', offset: 0, limit: 20 })
    assert.deepEqual(requests[1].params, { scope: 'synthetic', job_id: 18, offset: 20, limit: 20 })
    assert.deepEqual(requests[2].params, { scope: 'all', offset: 0, limit: 20 })
  })
  check('server filter denials and validation messages remain plain language', () => {
    assert.equal(analytics.postSelectionErrorMessage({ response: { data: { detail: 'Drive not found.' } } }), 'Drive not found.')
    assert.equal(analytics.postSelectionErrorMessage({ response: { data: { detail: [{ msg: 'Value error, Choose a valid record filter.' }] } } }), 'Choose a valid record filter.')
    assert(analytics.postSelectionErrorMessage({}).includes('Please retry'))
  })
  if (process.argv[2]) {
    const outputs = JSON.parse(readFileSync(process.argv[2], 'utf8'))
    const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#x27;')
    for (const scope of ['recorded', 'synthetic', 'all']) check(`actual local PostgreSQL ${scope} response renders milestones, reason provenance and limitations`, () => {
      const actual = outputs[scope], view = render(Content, { ...props, data: actual })
      assert.equal(actual.scope, scope)
      assert(view.includes(escape(actual.scope_explanation)) && !view.includes('undefined') && !view.includes('null%'))
      for (const row of [...actual.stages, ...actual.milestones, ...actual.closures]) assert(view.includes(escape(row.label)) && view.includes(escape(row.explanation)))
      for (const row of actual.stages.filter(item => item.previous_count !== null)) assert(view.includes(`${row.count} / ${row.previous_count}`))
      for (const row of actual.reasons) assert(view.includes(escape(row.reason || 'No audited reason recorded')))
      for (const limitation of actual.limitations) assert(view.includes(escape(limitation)))
      assert(view.includes(escape(actual.methodology)))
    })
  }
  console.log(`${passed} post-selection checks passed: SSR presentation, mocked authenticated transport${process.argv[2] ? ' and saved actual local PostgreSQL responses' : ''}. No live release or browser interaction claimed by this script.`)
} finally { await server.close() }
