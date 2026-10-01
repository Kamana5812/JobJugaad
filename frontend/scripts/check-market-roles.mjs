import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
const root = fileURLToPath(new URL('../', import.meta.url))
const catalogue = JSON.parse(readFileSync(new URL('../src/assets/market/roles.json', import.meta.url), 'utf8'))
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' })
let passed = 0
const check = (name, fn) => { fn(); passed++; console.log('PASS ' + name) }
try {
  const { default: Panel, MarketRoleCard, filterMarketRoles } = await server.ssrLoadModule('/src/pages/student/MarketRolesPanel.jsx')
  check('catalogue has source provenance and unique safe historical records', () => {
    assert.equal(catalogue.license, 'CC BY-SA 4.0'); assert.equal(catalogue.source_version, 13)
    assert.equal(catalogue.source_sha256.length, 64); assert.equal(new Set(catalogue.roles.map(r => r.id)).size, catalogue.roles.length)
    for (const r of catalogue.roles) { const u = new URL(r.original_url); assert.equal(u.protocol, 'https:'); assert(['www.linkedin.com','linkedin.com'].includes(u.hostname)); assert(u.pathname.startsWith('/jobs/view/')); assert(/^202[34]-/.test(r.listed_date)); assert(['Entry level','Internship'].includes(r.experience)); assert(!/\b(senior|sr|manager|director|lead|principal|chief)\b/i.test(r.title) && !r.title.includes('*')) }
  })
  check('search and exact location/experience filters compose', () => {
    const r = catalogue.roles[0]
    const matches = filterMarketRoles(catalogue.roles, r.title, r.location, r.experience)
    assert(matches.some(item => item.id === r.id))
    assert(filterMarketRoles(catalogue.roles, '', 'Nonexistent location', '').length === 0)
    assert(filterMarketRoles(catalogue.roles, 'zzzznonexistent', '', '').length === 0)
    assert.deepEqual(filterMarketRoles(catalogue.roles, '  ', '', ''), catalogue.roles)
  })
  check('every card preserves descriptions and clearly labels its external historical link', () => {
    for (const role of catalogue.roles) {
      const html = renderToStaticMarkup(React.createElement(MarketRoleCard, { role }))
      assert(html.includes('Historical reference') && html.includes('Availability has not been checked'))
      assert(html.includes(role.original_url.replaceAll('&','&amp;')) && html.includes('noopener noreferrer'))
      assert(html.includes('not verified mandatory requirements') && html.includes('Read source description'))
      assert(!html.includes('<button') && !html.includes('Match score'))
    }
  })
  check('description text cannot inject HTML into the card', () => {
    const html = renderToStaticMarkup(React.createElement(MarketRoleCard, { role: {...catalogue.roles[0], description:'<script>alert(1)</script>'} }))
    assert(html.includes('&lt;script&gt;') && !html.includes('<script>alert'))
  })
  check('panel keeps market references distinct from live drives and attributes adapted data', () => {
    const html = renderToStaticMarkup(React.createElement(Panel))
    assert(html.includes('not current vacancies, college drives, or employer partnerships'))
    assert(html.includes('CC BY-SA 4.0') && html.includes('Arsh Koneru') && html.includes('Zoey Yuzou'))
    assert(html.includes('not a representative market survey') && html.includes('No application is submitted'))
    assert.equal((html.match(/Read source description/g) || []).length, 6)
  })
  console.log(passed + ' market-reference checks passed; component rendering, not browser interaction.')
} finally { await server.close() }
