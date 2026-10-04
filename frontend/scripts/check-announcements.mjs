import assert from 'node:assert/strict'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'

const root = fileURLToPath(new URL('../', import.meta.url))
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' })
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props))
try {
  const compose = await server.ssrLoadModule('/src/pages/admin/AnnouncementCompose.jsx')
  const draft = { job_id: '12', audience: 'applicants', branch: '  computer   science ', kind: 'update', title: '  Interview preparation  ', body: '  Review the venue and bring your identification.\nCheck the drive details.  ' }
  const input = compose.announcementInput(draft)
  assert.equal(input.job_id, 12)
  assert.equal(input.branch, 'COMPUTER SCIENCE')
  assert.equal(input.title, 'Interview preparation')
  assert(input.body.includes('\n'))
  assert.equal(compose.announcementInput({ ...draft, branch: '' }).branch, null)
  assert.throws(() => compose.announcementInput({ ...draft, job_id: '' }), /Choose a drive/)
  assert.throws(() => compose.announcementInput({ ...draft, title: '   ' }), /at least 3/)
  assert.throws(() => compose.announcementInput({ ...draft, body: '         ' }), /at least 10/)
  const preview = { ...input, job_title: 'Recorded engineering drive', company_name: 'Recorded company', recipient_count: 2, sample: [{ student_id: 5, name: 'Preview student', branch: 'COMPUTER SCIENCE' }], preview_hash: 'a'.repeat(64), explanation: 'Current approved students with a recorded active application in this drive.' }
  const key = '51e2a74f-a129-44a2-98b2-a3fc65f85b92'
  const publish = compose.publicationInput(preview, key)
  assert.deepEqual(Object.keys(publish).sort(), ['audience', 'body', 'branch', 'idempotency_key', 'job_id', 'kind', 'preview_hash', 'title'].sort())
  assert.equal(publish.preview_hash, preview.preview_hash)
  assert.equal(publish.idempotency_key, key)
  assert.deepEqual(compose.publicationInput(preview, key), publish)
  const Preview = (await server.ssrLoadModule('/src/pages/admin/AnnouncementPreview.jsx')).default
  const props = { preview, reviewed: false, onReviewed: () => {}, onPublish: () => {}, busy: false, retry: false }
  assert.match(render(Preview, props), /<button[^>]*disabled=""/)
  assert(!render(Preview, { ...props, reviewed: true }).match(/<button[^>]*disabled=""/))
  assert.match(render(Preview, { ...props, reviewed: true, busy: true }), /<button[^>]*disabled=""/)
  const empty = render(Preview, { ...props, preview: { ...preview, recipient_count: 0, sample: [] }, reviewed: true })
  assert(empty.includes('No recipients currently match') && empty.match(/<button[^>]*disabled=""/))
  assert(render(Preview, { ...props, reviewed: true, retry: true }).includes('Retry the same publication'))
  const unsafe = { ...preview, title: '<img src=x onerror=alert(1)>', body: '<script>alert("not markup")</script>\nSecond line.' }
  const escapedPreview = render(Preview, { ...props, preview: unsafe })
  assert(escapedPreview.includes('&lt;script&gt;') && !escapedPreview.includes('<script>') && escapedPreview.includes('whitespace-pre-wrap'))
  assert(escapedPreview.includes(preview.explanation))
  const Record = (await server.ssrLoadModule('/src/pages/admin/AnnouncementHistory.jsx')).AnnouncementRecord
  const history = render(Record, { item: { ...unsafe, id: 2, published_by: 9, published_at: '2026-10-04T09:00:00Z', read_count: 1 } })
  assert(history.includes('2 recorded recipient(s)') && history.includes('1 read in-app') && history.includes('&lt;script&gt;'))
  assert(history.includes('Administrator #9'))
  assert(!history.includes('Delete') && !history.includes('Edit announcement'))
  const api = (await server.ssrLoadModule('/src/api/client.js')).api
  const announcements = await server.ssrLoadModule('/src/api/announcements.js')
  assert.equal(announcements.announcementErrorMessage({ response: { data: { detail: [{ msg: 'Value error, Preview the current audience again.' }] } } }), 'Preview the current audience again.')
  const requests = []
  api.defaults.adapter = async config => { requests.push({ method: config.method, url: config.url, params: config.params, body: config.data ? JSON.parse(config.data) : undefined }); return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config } }
  await announcements.getAnnouncementOptions()
  await announcements.previewAnnouncement(input)
  await announcements.publishAnnouncement(publish)
  await announcements.getAnnouncements(20)
  await announcements.getAnnouncementRecipients(2, 10)
  assert.deepEqual(requests.map(({ method, url }) => [method, url]), [['get', '/admin/announcements/options'], ['post', '/admin/announcements/preview'], ['post', '/admin/announcements'], ['get', '/admin/announcements'], ['get', '/admin/announcements/2/recipients']])
  assert.deepEqual(requests[1].body, input)
  assert.deepEqual(requests[2].body, publish)
  assert.deepEqual(requests[3].params, { offset: 20, limit: 10 })
  assert.deepEqual(requests[4].params, { offset: 10, limit: 10 })
  const NotificationItem = (await server.ssrLoadModule('/src/components/NotificationsPage.jsx')).NotificationItem
  const notification = { id: 2, title: unsafe.title, body: unsafe.body, kind: 'drive_reminder', created_at: '2026-10-04T09:00:00Z', read_at: null, target_path: '/student#applications' }
  const feed = render(MemoryRouter, { children: React.createElement(NotificationItem, { item: notification, busy: false, onRead: () => {} }) })
  assert(feed.includes('Manual drive reminder') && feed.includes('&lt;script&gt;') && feed.includes('href="/student#applications"'))
  const unknownLink = render(MemoryRouter, { children: React.createElement(NotificationItem, { item: { ...notification, target_path: 'https://unexpected.example/' }, busy: false, onRead: () => {} }) })
  assert(!unknownLink.includes('unexpected.example'))
  console.log('Announcement checks passed: input normalization/validation; reviewed/nonempty/busy publication gates; frozen publication payload and retry key; escaped multiline preview/history/feed; existing related-link allowlist; 5 mocked API wrapper methods/paths, payloads and paging. No browser interaction or live publication claimed.')
} finally { await server.close() }
