import assert from 'node:assert/strict'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const root = fileURLToPath(new URL('../', import.meta.url))
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' })
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props))
try {
  const windows = await server.ssrLoadModule('/src/components/CalendarWindowFields.jsx')
  process.env.TZ = 'Asia/Kolkata'
  const input = windows.windowInput({ kind: 'available', label: '  Interview availability  ', starts_at: '2026-10-10T09:00', ends_at: '2026-10-10T10:00' })
  assert(input.starts_at.endsWith('Z') && input.ends_at.endsWith('Z'))
  assert.equal(input.starts_at, '2026-10-10T03:30:00.000Z')
  assert.equal(new Date(input.ends_at) - new Date(input.starts_at), 3600000)
  assert.equal(input.label, 'Interview availability')
  assert.throws(() => windows.windowInput({ kind: 'unavailable', label: 'Exam preparation', starts_at: '2026-10-10T10:00', ends_at: '2026-10-10T09:00' }), /end time later/)
  assert.throws(() => windows.windowInput({ kind: 'available', label: '  ', starts_at: '2026-10-10T09:00', ends_at: '2026-10-10T10:00' }), /at least 3/)
  const fields = render(windows.default, { form: { ...windows.initialWindow(), label: 'Available for interview' }, change: () => () => {} })
  assert(fields.includes('datetime-local') && !fields.includes('Exam block'))
  const item = { id: 3, college_id: 1, kind: 'available', scope: 'student', student_id: 1, resource_name: null, starts_at: '2026-10-10T03:30:00Z', ends_at: '2026-10-10T04:30:00Z', label: 'Interview availability', status: 'active', version: 1 }
  const constraints = (await server.ssrLoadModule('/src/components/CalendarConstraintList.jsx')).default
  const active = render(constraints, { data: { items: [item], total: 1, offset: 0, limit: 20 }, busy: false, onCancel: async () => {} })
  assert(active.includes('Cancellation reason for entry #3') && active.includes('minLength="10"'))
  const cancelled = render(constraints, { data: { items: [{ ...item, status: 'cancelled' }], total: 1 }, busy: false, onCancel: async () => {} })
  assert(cancelled.includes('cancelled') && !cancelled.includes('Confirm cancellation'))
  const proposal = (await server.ssrLoadModule('/src/pages/admin/ProposalCard.jsx')).default
  const names = { student: () => 'Scheduling test student', job: () => 'Scheduling test drive' }
  const record = { id: 6, job_id: 1, student_id: 1, requested_time: item.starts_at, scheduled_time: item.starts_at, end_time: item.ends_at, venue: 'Room 1', panel_id: 'Panel 1', round_number: 2, round_name: 'Technical interview', version: 1, conflicts: [], explanation: 'Next clear slot proposed for administrator review.', calendar_conflicts: [{ constraint_id: 4, kind: 'exam', explanation: 'The proposed student has a recorded branch exam block.', starts_at: item.starts_at, ends_at: item.ends_at }] }
  const proposalHtml = render(proposal, { proposal: record, names, perform: async () => {}, busy: false })
  assert(proposalHtml.includes('Round 2') && proposalHtml.includes('Technical interview'))
  assert(proposalHtml.includes('Calendar constraints') && proposalHtml.includes(record.calendar_conflicts[0].explanation))
  const list = (await server.ssrLoadModule('/src/pages/admin/InterviewList.jsx')).default
  const bookingHtml = render(list, { items: [{ ...record, status: 'scheduled' }], names, onResolve: () => {}, perform: async () => {}, busy: false })
  assert(bookingHtml.includes('Round 2') && bookingHtml.includes('Technical interview'))
  const scheduleForm = (await server.ssrLoadModule('/src/pages/admin/ScheduleForm.jsx')).default
  const reschedule = render(scheduleForm, { source: record, board: { jobs: [{ id: 1, name: 'Test drive' }], students: [{ id: 1, name: 'Test student' }] }, onClearSource: () => {}, onSaved: async () => {} })
  assert.match(reschedule, /<input[^>]*disabled=""[^>]*value="2"/)
  assert.match(reschedule, /<input[^>]*disabled=""[^>]*value="Technical interview"/)
  const client = (await server.ssrLoadModule('/src/api/client.js')).api
  const calendar = await server.ssrLoadModule('/src/api/calendar.js')
  assert.equal(calendar.calendarErrorMessage({ response: { data: { detail: [{ msg: 'Value error, Choose a valid campus timezone.' }] } } }), 'Choose a valid campus timezone.')
  const requests = []
  client.defaults.adapter = async config => {
    requests.push({ method: config.method, url: config.url, params: config.params, body: config.data ? JSON.parse(config.data) : undefined })
    return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config }
  }
  await calendar.getCalendarSettings()
  await calendar.saveCalendarSettings({ version: 3, enabled: false, require_student_availability: true, reason: 'Reviewed campus policy' })
  await calendar.getCalendarConstraints(40)
  await calendar.createCalendarConstraint({ ...input, scope: 'student', student_id: 1, resource_name: null, reason: 'Student calendar update' })
  await calendar.cancelCalendarConstraint(3, { version: 2, reason: 'Replaced expired availability' })
  await calendar.getStudentAvailability(1, 20)
  await calendar.createStudentAvailability(1, input)
  await calendar.cancelStudentAvailability(1, 3, { version: 4, reason: 'Replaced expired availability' })
  assert.deepEqual(requests.map(({ method, url }) => [method, url]), [
    ['get', '/admin/calendar/settings'], ['put', '/admin/calendar/settings'], ['get', '/admin/calendar/constraints'], ['post', '/admin/calendar/constraints'], ['put', '/admin/calendar/constraints/3/cancel'], ['get', '/students/1/availability'], ['post', '/students/1/availability'], ['put', '/students/1/availability/3/cancel']
  ])
  assert.deepEqual(requests[2].params, { offset: 40, limit: 20 })
  assert.deepEqual(requests[5].params, { offset: 20, limit: 10 })
  assert.equal(requests[1].body.version, 3)
  assert.equal(requests[1].body.enabled, false)
  assert.equal(requests[1].body.require_student_availability, true)
  assert.equal(requests[4].body.version, 2)
  assert.equal(requests[7].body.version, 4)
  assert.deepEqual(requests[6].body, input)
  console.log('Calendar UI checks passed: Asia/Kolkata dates become UTC; invalid windows/blank labels rejected; active/cancelled history controls differ; round identity remains disabled on reschedule; calendar explanations render; 8 API wrapper methods, paths, pagination and cancellation versions checked with a mocked Axios adapter. Not a browser interaction test or live request.')
} finally { await server.close() }
