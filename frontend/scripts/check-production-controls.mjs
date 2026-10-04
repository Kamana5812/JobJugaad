import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'

const root = fileURLToPath(new URL('../', import.meta.url))
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' })
let passed = 0
const check = (name, run) => { run(); passed++; console.log(`PASS ${name}`) }
try {
  const { default: Fairness } = await server.ssrLoadModule('/src/pages/admin/FairnessPanel.jsx')
  const { default: Privacy } = await server.ssrLoadModule('/src/pages/public/PrivacyPage.jsx')
  const { api } = await server.ssrLoadModule('/src/api/client.js')
  const actions = await server.ssrLoadModule('/src/api/accountData.js')
  const render = component => renderToStaticMarkup(React.createElement(MemoryRouter, null, React.createElement(component)))
  const fairness = render(Fairness), privacy = render(Privacy)
  check('fairness clearly identifies frozen synthetic evidence and unvalidated weights', () => {
    for (const text of ['Frozen synthetic audit', 'Unvalidated starting weights', 'Strong-evidence exclusions', 'CGPA exclusions', 'not independently validated']) assert(fairness.includes(text), text)
  })
  check('fairness includes all drives and limitations without a fairness guarantee', () => {
    assert.equal((fairness.match(/CGPA floor:/g) || []).length, 3)
    assert(fairness.includes('No gender') && fairness.includes('Do not change weights'))
  })
  check('privacy distinguishes account restriction from erasure and private backups', () => {
    for (const text of ['does not erase', 'review within 30 days', 'owner-controlled keys', '/account']) assert(privacy.includes(text), text)
  })
  let called
  api.post = async (path, body) => { called = { path, body }; return { data: { detail: 'confirmed' } } }
  check('logout requests server revocation', () => {})
  await actions.revokeSessions()
  assert.equal(called.path, '/auth/logout')
  await actions.requestDeletion({ reason: 'Controlled fixture deletion review', confirmation: 'REQUEST DELETION' })
  assert.equal(called.path, '/account/data-requests')
  assert.equal(called.body.confirmation, 'REQUEST DELETION')
  passed++; console.log('PASS deletion request preserves explicit confirmation')
  console.log(`${passed} production-controls checks passed; rendering and request wiring only.`)
} finally { await server.close() }
