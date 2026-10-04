import assert from 'node:assert/strict'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const root = fileURLToPath(new URL('../', import.meta.url))
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' })
const render = (component, props) => renderToStaticMarkup(React.createElement(component, props))
try {
  const rules = await server.ssrLoadModule('/src/components/offerDocumentRules.js')
  const draft = { id: 51, student_id: 19, version: 8, offer_letter_status: 'draft', documents_status: 'pending', verification_status: 'pending', acceptance_status: 'pending', joining_status: 'pending', audit: [] }
  const issued = { ...draft, offer_letter_status: 'issued' }
  const submitted = { ...issued, documents_status: 'submitted' }
  const changes = { ...issued, documents_status: 'changes_requested' }
  const closed = { ...issued, acceptance_status: 'declined' }
  const file = { id: 72, offer_id: 51, kind: 'offer_letter', label: 'Private letter', original_filename: 'private.pdf', size_bytes: 3456, page_count: 1, sha256: 'a'.repeat(64), uploaded_by: 3, uploaded_at: '2026-10-04T09:00:00Z', uploaded_offer_version: 8, is_active: true, review_status: 'pending', reviewed_by: null, reviewed_at: null, review_reason: null, supersedes_document_id: null }
  assert(rules.canUploadOfferDocument(draft, true))
  assert(!rules.canUploadOfferDocument(draft, false) && !rules.canUploadOfferDocument(issued, true))
  assert(rules.canUploadOfferDocument(issued, false) && rules.canUploadOfferDocument(changes, false))
  assert(!rules.canUploadOfferDocument(submitted, false) && !rules.canUploadOfferDocument(closed, false))
  assert(rules.canReviewOfferDocument(file, draft, true))
  assert(!rules.canReviewOfferDocument(file, issued, true) && !rules.canReviewOfferDocument(file, draft, false))
  const supporting = { ...file, kind: 'supporting_document' }
  assert(rules.canReviewOfferDocument(supporting, submitted, true))
  assert(!rules.canReviewOfferDocument(supporting, issued, true))
  assert(!rules.canReviewOfferDocument({ ...supporting, is_active: false }, submitted, true))
  assert(!rules.canReviewOfferDocument({ ...supporting, review_status: 'rejected' }, submitted, true))
  assert(!rules.canReviewOfferDocument(supporting, { ...submitted, joining_status: 'joined' }, true))
  assert(!rules.studentLetterAvailable(draft) && rules.studentLetterAvailable(issued))
  const withdrawnIssued = { ...draft, offer_letter_status: 'withdrawn', audit: [{ action: 'offer_letter_status:issued' }] }
  assert(rules.studentLetterAvailable(withdrawnIssued))

  const limits = { max_bytes: 2 * 1024 * 1024, max_pages: 20, max_files: 10, max_offer_bytes: 10 * 1024 * 1024, stored_files: 2, stored_bytes: 2000 }
  const pdf = new File(['%PDF-1.7 fixture'], 'support.pdf', { type: 'application/pdf' })
  const form = { label: '  Enrollment proof  ', reason: '  Reviewed enrollment evidence for this offer.  ', replaces_document_id: '72' }
  const nonce = 'c93c7f50-16cb-49ab-9a60-e3af840dc2e3'
  const input = rules.uploadDocumentInput(pdf, form, 8, limits, nonce)
  assert.equal(input.file, pdf)
  assert.equal(input.version, 8)
  assert.equal(input.label, 'Enrollment proof')
  assert.equal(input.reason, 'Reviewed enrollment evidence for this offer.')
  assert.equal(input.replaces_document_id, 72)
  assert.equal(input.idempotency_key, nonce)
  assert.equal(rules.uploadDocumentInput(pdf, { ...form, replaces_document_id: '' }, 8, limits, nonce).replaces_document_id, null)
  assert.throws(() => rules.uploadDocumentInput(null, form, 8, limits, nonce), /non-empty PDF/)
  assert.throws(() => rules.uploadDocumentInput(new File([], 'empty.pdf'), form, 8, limits, nonce), /non-empty PDF/)
  assert.throws(() => rules.uploadDocumentInput(new File(['x'], 'proof.html'), form, 8, limits, nonce), /\.pdf extension/)
  assert.throws(() => rules.uploadDocumentInput(new File([new Uint8Array(limits.max_bytes + 1)], 'large.pdf'), form, 8, limits, nonce), /no larger than/)
  assert.throws(() => rules.uploadDocumentInput(pdf, form, 8, { ...limits, stored_files: 10 }, nonce), /retained-file storage/)
  assert.throws(() => rules.uploadDocumentInput(pdf, form, 8, { ...limits, stored_bytes: limits.max_offer_bytes }, nonce), /retained-file storage/)
  assert.throws(() => rules.uploadDocumentInput(pdf, { ...form, label: '  ' }, 8, limits, nonce), /label between/)
  assert.throws(() => rules.uploadDocumentInput(pdf, { ...form, reason: '  short  ' }, 8, limits, nonce), /reason between/)

  const Record = (await server.ssrLoadModule('/src/components/OfferDocumentRecord.jsx')).default
  const props = { file, offer: draft, admin: true, version: 8, disabled: false, onSaved: () => {}, onLockChange: () => {} }
  const draftCard = render(Record, props)
  assert(draftCard.includes('Draft letter file. It has not been issued') && draftCard.includes('Record human file review'))
  assert(draftCard.includes('Download private PDF #72') && !draftCard.includes('href=') && !draftCard.includes('<iframe') && !draftCard.includes('<embed'))
  assert.equal(render(Record, { ...props, admin: false }), '')
  const studentCard = render(Record, { ...props, admin: false, offer: issued })
  assert(studentCard.includes('Download private PDF #72') && !studentCard.includes('Record human file review'))
  const oldCard = render(Record, { ...props, file: { ...file, is_active: false } })
  assert(oldCard.includes('Superseded file') && !oldCard.includes('Record human file review'))
  assert(!render(Record, { ...props, file: { ...file, review_status: 'verified' } }).includes('Record human file review'))
  const unsafe = { ...file, label: '<img src=x onerror=alert(1)>', original_filename: '<script>name</script>.pdf', reviewed_at: '2026-10-04T09:05:00Z', review_reason: '<script>private reason</script>\nSecond line.' }
  const escaped = render(Record, { ...props, file: unsafe })
  assert(escaped.includes('&lt;script&gt;') && escaped.includes('&lt;img') && !escaped.includes('<script>') && escaped.includes('whitespace-pre-wrap'))
  const Upload = (await server.ssrLoadModule('/src/components/OfferDocumentUpload.jsx')).default
  const upload = render(Upload, { offer: draft, admin: true, data: { items: [file], offer_version: 8, limits }, disabled: true, onSaved: () => {}, onLockChange: () => {} })
  assert(upload.includes('Upload a draft offer letter PDF') && upload.includes('fieldset disabled=""') && upload.includes('antivirus') === false)
  assert(upload.includes('Issuance, document submission and verification remain separate human actions'))
  const uploadProps = { data: { items: [file], offer_version: 8, limits }, disabled: false, onSaved: () => {}, onLockChange: () => {} }
  assert.equal(render(Upload, { ...uploadProps, offer: issued, admin: true }), '')
  assert.equal(render(Upload, { ...uploadProps, offer: closed, admin: true }), '')
  assert.equal(render(Upload, { ...uploadProps, offer: draft, admin: false }), '')
  assert.equal(render(Upload, { ...uploadProps, offer: submitted, admin: false }), '')
  assert.equal(render(Upload, { ...uploadProps, offer: { ...issued, joining_status: 'joined' }, admin: false }), '')
  assert(render(Upload, { ...uploadProps, offer: issued, admin: false }).includes('Upload a supporting PDF'))
  assert(render(Upload, { ...uploadProps, offer: changes, admin: false }).includes('Upload a supporting PDF'))
  const Actions = (await server.ssrLoadModule('/src/components/OfferActions.jsx')).default
  const stage = render(Actions, { offer: issued, admin: false, disabled: true, onSaved: () => {} })
  assert(stage.includes('file upload/review does not perform this stage action') && stage.match(/<button[^>]*disabled=""/))

  const api = (await server.ssrLoadModule('/src/api/client.js')).api
  const docs = await server.ssrLoadModule('/src/api/offerDocuments.js')
  assert.equal(docs.offerDocumentErrorMessage({ response: { data: { detail: [{ msg: 'Value error, Choose a valid PDF.' }] } } }), 'Choose a valid PDF.')
  const requests = []
  api.defaults.headers.common.Authorization = 'Bearer local-transport-fixture'
  api.defaults.adapter = async config => {
    requests.push({ method: config.method, url: config.url, params: config.params, responseType: config.responseType, authorization: config.headers.get('Authorization'), body: config.data instanceof FormData ? config.data : config.data ? JSON.parse(config.data) : undefined })
    return { data: config.responseType === 'blob' ? new Blob(['%PDF fixture']) : { ok: true }, status: 200, statusText: 'OK', headers: {}, config }
  }
  await docs.getOfferDocuments(51, null, 10)
  await docs.getOfferDocuments(51, 19, 0)
  await docs.getOfferDocumentEvents(51, 72, 19, 10)
  await docs.uploadOfferDocument(51, null, input)
  await docs.uploadOfferDocument(51, 19, input)
  await docs.uploadOfferDocument(51, 19, input)
  await docs.reviewOfferDocument(51, 72, { version: 8, review_status: 'verified', reason: 'Human reviewed this uploaded letter.' })
  const blob = await docs.downloadOfferDocument(51, 72, 19)
  assert.deepEqual(requests.map(({ method, url }) => [method, url]), [['get', '/admin/offers/51/documents'], ['get', '/students/19/offers/51/documents'], ['get', '/students/19/offers/51/documents/72/events'], ['post', '/admin/offers/51/documents'], ['post', '/students/19/offers/51/documents'], ['post', '/students/19/offers/51/documents'], ['post', '/admin/offers/51/documents/72/review'], ['get', '/students/19/offers/51/documents/72/download']])
  assert.deepEqual(requests[0].params, { offset: 10, limit: 10 })
  assert.deepEqual(requests[2].params, { offset: 10, limit: 10 })
  for (const request of requests) assert.equal(request.authorization, 'Bearer local-transport-fixture')
  assert.equal(requests[3].body.get('kind'), 'offer_letter')
  assert(!requests[4].body.has('kind'))
  assert.equal(requests[4].body.get('file').name, 'support.pdf')
  for (const field of ['version', 'reason', 'label', 'idempotency_key', 'replaces_document_id']) assert.equal(requests[4].body.get(field), String(input[field]))
  assert.equal(requests[5].body.get('idempotency_key'), requests[4].body.get('idempotency_key'))
  assert.deepEqual(requests[6].body, { version: 8, review_status: 'verified', reason: 'Human reviewed this uploaded letter.' })
  assert.equal(requests[7].responseType, 'blob')
  assert.equal(requests[7].params, undefined)
  assert(blob instanceof Blob)
  const denied = { isAxiosError: true, response: { status: 403, data: new Blob([JSON.stringify({ detail: 'This private file is unavailable to this account.' })], { type: 'application/json' }) } }
  api.defaults.adapter = async () => { throw denied }
  await assert.rejects(() => docs.downloadOfferDocument(51, 72, 19), error => docs.offerDocumentErrorMessage(error) === 'This private file is unavailable to this account.')

  const originalDocument = globalThis.document, originalCreate = URL.createObjectURL, originalRevoke = URL.revokeObjectURL, originalTimeout = globalThis.setTimeout
  const downloadEvents = [], anchor = { click: () => downloadEvents.push('clicked'), remove: () => downloadEvents.push('removed') }
  try {
    globalThis.document = { createElement: tag => { assert.equal(tag, 'a'); return anchor }, body: { appendChild: item => { assert.equal(item, anchor); downloadEvents.push('attached') } } }
    URL.createObjectURL = value => { assert.equal(value, blob); return 'blob:private-fixture' }
    URL.revokeObjectURL = value => { assert.equal(value, 'blob:private-fixture'); downloadEvents.push('revoked') }
    globalThis.setTimeout = callback => callback()
    docs.saveDownloadedPdf(blob, 51, 72)
    assert.equal(anchor.download, 'offer-document-72.pdf')
    assert.equal(anchor.href, 'blob:private-fixture')
    assert.deepEqual(downloadEvents, ['attached', 'clicked', 'removed', 'revoked'])
  } finally { globalThis.document = originalDocument; URL.createObjectURL = originalCreate; URL.revokeObjectURL = originalRevoke; globalThis.setTimeout = originalTimeout }
  console.log('Private offer PDF checks passed: role/stage/active-file review gates; hidden student draft letters; retained-file size/count limits; escaped metadata and human reasons; versioned multipart/admin-only kind; authenticated Blob download and JSON errors; safe generated filename and Blob cleanup. SSR and mocked transport only; no real upload, browser retry, or live review claimed.')
} finally { await server.close() }
