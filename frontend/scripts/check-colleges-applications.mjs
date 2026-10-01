import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
const root = fileURLToPath(new URL('../', import.meta.url))
const directory = JSON.parse(readFileSync(new URL('../src/assets/bput-colleges.json', import.meta.url), 'utf8'))
const data = JSON.parse(readFileSync(new URL('../../.local/dashboard-render-data.json', import.meta.url), 'utf8'))
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' })
const render = (C, props) => renderToStaticMarkup(React.createElement(C, props))
const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#x27;')
let passed = 0
const check = (name, fn) => { fn(); passed++; console.log('PASS ' + name) }
try {
 const College = (await server.ssrLoadModule('/src/components/CollegeSelector.jsx')).default
 const Hero = (await server.ssrLoadModule('/src/components/PortalHero.jsx')).default
 const Card = (await server.ssrLoadModule('/src/components/ApplicationCard.jsx')).default
 const Action = (await server.ssrLoadModule('/src/components/ApplicationAction.jsx')).default
 const college = directory.colleges.find(c => c.kind === 'bput_directory')
 check('official snapshot, 169 colleges, stable IDs and demo accounts preserved', () => {
   assert.equal(directory.colleges.filter(c => c.kind === 'bput_directory').length, 169)
   assert.deepEqual(directory.colleges.slice(0, 2).map(c => c.id), [1, 2])
   for (const c of directory.colleges.slice(2)) assert.equal(c.id, 10000 + Number(c.code))
   assert.equal(new Set(directory.colleges.map(c => c.id)).size, 171)
 })
 check('search and college selector render official names and honest enrollment/source notice', () => {
   const html = render(College, { value: college.id, onChange() {} })
   assert(html.includes('Find your college') && html.includes('2022–23 snapshot') && html.includes('administrator approval'))
   assert(html.includes(esc(college.name)) && html.includes(directory.source_url))
   assert(!html.includes('Demo College 1') && !html.includes('Demo College 2'))
   const legacy = render(College, { value: 1, allowDemo: true, onChange() {} })
   assert(legacy.includes('Demo College 1') && legacy.includes('Demo College 2'))
   assert(html.includes(`value="${college.id}" selected=""`))
 })
 check('workspace names selected real college rather than inventing a demo name', () => {
   const html = render(Hero, { role: 'student', collegeId: college.id })
   assert(html.includes(esc(college.name)) && !html.includes(`Demo College ${college.id}`))
 })
 // Rendering fixture uses saved database-backed matching evidence, not claimed live application data.
 const a = { id: 1, student_id: 1, student_name: '<Synthetic student>', job_id: 1,
   job_title: 'Synthetic role', company_name: 'Synthetic company', status: 'submitted', version: 1,
   cover_note: '<script>alert(1)</script>', created_at: '2026-10-02T10:00:00Z',
   explanation: 'Submission-time evidence; human review remains separate.', evidence: data.opportunities.target,
   history: [{ id: 1, previous_status: null, status: 'submitted', reason: 'Synthetic application submitted', created_at: '2026-10-02T10:00:00Z' }] }
 check('application score always includes complete factors, explanation, gaps and next step', () => {
   const html = render(Card, { application: a })
   assert(html.includes(esc(a.evidence.explanation)) && html.includes(esc(a.evidence.next_step)) && html.includes(esc(a.evidence.methodology)))
   for (const f of a.evidence.factor_breakdown) assert(html.includes(esc(f.label)) && html.includes(esc(f.evidence)))
   assert(html.includes('Submission-time match') && html.includes('Status history'))
   assert(html.includes('&lt;script&gt;') && !html.includes('<script>'))
 })
 check('review records reason and distinguishes shortlist from interview or offer', () => {
   const html = render(Action, { application: a, recruiter: true, onAction() {}, onSaved() {}, onExpired() {} })
   assert(html.includes('visible to the student') && html.includes('does not schedule an interview or issue an offer'))
   assert(html.includes('Reason / next step') && html.includes('minLength="5"'))
 })
 check('withdrawal closure and terminal statuses are explicit', () => {
   assert(render(Action, { application: a }).includes('cannot submit again'))
   assert(render(Action, { application: { ...a, status: 'rejected' } }).includes('application is closed'))
   assert(render(Action, { application: { ...a, status: 'withdrawn' } }).includes('application is closed'))
 })
 console.log(`${passed} college/application interface checks passed; no browser-click verification claimed.`)
} finally { await server.close() }
