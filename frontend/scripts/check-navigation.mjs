import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'

const root = fileURLToPath(new URL('../', import.meta.url))
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' })
const h = React.createElement
const render = (Component, props = {}) => renderToStaticMarkup(h(MemoryRouter, null, h(Component, props)))
let passed = 0
const check = (name, fn) => { fn(); passed++; console.log(`PASS ${name}`) }
try {
  const { RoleSelection, RoleAuthScreen } = await server.ssrLoadModule('/src/pages/public/AuthPage.jsx')
  const { default: LandingPage } = await server.ssrLoadModule('/src/pages/public/LandingPage.jsx')
  const { roleHome, validRole } = await server.ssrLoadModule('/src/context/roleHome.js')
  const { RoleGate } = await server.ssrLoadModule('/src/components/RoleGuard.jsx')
  const { authenticateAccount } = await server.ssrLoadModule('/src/api/authentication.js')
  const { api } = await server.ssrLoadModule('/src/api/client.js')
  const example = JSON.parse(readFileSync(new URL('../src/assets/matching-example.json', import.meta.url), 'utf8'))
  const evaluation = JSON.parse(readFileSync(new URL('../../evaluations/phase4-results.json', import.meta.url), 'utf8'))
  check('role selector contains three role links and no form fields', () => {
    const html = render(RoleSelection)
    assert(!html.includes('<input') && !html.includes('<form') && !html.includes('<select'))
    for (const role of ['student','recruiter','admin']) assert(html.includes(`/auth?role=${role}&amp;mode=login`))
  })
  check('signup selector never offers admin signup', () => {
    const html = render(RoleSelection, { mode: 'signup' })
    assert(html.includes('/auth?role=student&amp;mode=signup'))
    assert(html.includes('/auth?role=recruiter&amp;mode=signup'))
    assert(html.includes('/auth?role=admin&amp;mode=login'))
    assert(!html.includes('role=admin&amp;mode=signup'))
  })
  for (const role of ['student','recruiter','admin']) for (const signup of [false,true]) {
    check(`${role} ${signup ? 'signup' : 'login'} displays only appropriate fields`, () => {
      const html = render(RoleAuthScreen, { role, signup, onAuthenticated() {} })
      assert(html.includes('type="password"') && html.includes('Demo college'))
      assert.equal(html.includes('Full name'), signup && role === 'student')
      assert.equal(html.includes('Company name'), signup && role === 'recruiter')
      assert.equal(html.includes('Industry'), signup && role === 'recruiter')
      if (role === 'admin') assert(html.includes('Public admin signup is not available') && !html.includes('Create admin account'))
    })
  }
  check('landing links point to selector or preselected roles and contain explained synthetic evidence', () => {
    const html = render(LandingPage)
    for (const role of ['student','recruiter','admin']) assert(html.includes(`/auth?role=${role}`))
    assert(html.includes('href="/auth"') && html.includes('Below Threshold:'))
    assert(html.includes('Saved synthetic example') && html.includes('Your Next Jugaad'))
    for (const factor of example.factor_breakdown) assert(html.includes(factor.label))
    assert(html.includes('unvalidated assumptions') && !html.includes('AI-powered'))
  })
  check('landing example is unchanged engine evidence, with contributions equal to score', () => {
    const saved = evaluation.cases[0].matching_evidence[0]
    assert.deepEqual(example.factor_breakdown, saved.factor_breakdown)
    assert.equal(example.explanation, saved.explanation)
    assert.equal(example.match_score, saved.match_score)
    assert(Math.abs(example.factor_breakdown.reduce((sum,f) => sum+f.contribution,0)-example.match_score) < 1e-8)
  })
  check('verified roles map to exact requested routes, invalid roles get no dashboard', () => {
    assert.equal(roleHome('student'), '/student'); assert.equal(roleHome('recruiter'), '/recruiter'); assert.equal(roleHome('admin'), '/admin')
    assert.equal(roleHome('superadmin'), '/auth'); assert.equal(validRole('__proto__'), null); assert.equal(roleHome('__proto__'), '/auth'); assert.equal(roleHome('constructor'), '/auth')
  })
  check('every dashboard blocks anonymous and wrong-role access while allowing its own role', () => {
    for (const role of ['student','recruiter','admin']) {
      assert.equal(RoleGate({ user:null, loading:false, role, children:'private' }).props.to, `/auth?role=${role}&mode=login`)
      assert.equal(RoleGate({ user:{role}, loading:false, role, children:'private' }), 'private')
      assert.notEqual(RoleGate({ user:{role}, loading:true, role, children:'private' }), 'private')
      for (const actual of ['student','recruiter','admin'].filter(r=>r!==role)) {
        assert.equal(RoleGate({ user:{role:actual}, loading:false, role, children:'private' }).props.to, roleHome(actual))
      }
    }
  })
  // A recording Axios adapter tests request wiring only; these are not live backend tests.
  const form = { name:'Synthetic example', industry:'Testing', email:'example@example.invalid', password:'Synthetic-Test-Only', college_id:'2' }
  for (const role of ['student','recruiter','admin']) for (const signup of [false,true]) {
    let request
    api.defaults.adapter = async config => {
      request = {url:config.url, data:JSON.parse(config.data)}
      return {data:{access_token:'test-only',user:{role:'admin'}},status:200,statusText:'OK',headers:{},config}
    }
    const result = await authenticateAccount(role,signup,form)
    check(`${role} ${signup ? 'signup' : 'login'} calls existing endpoint and honors returned role`, () => {
      const expected = !signup || role==='admin' ? '/auth/login' : role==='student' ? '/auth/signup' : '/auth/recruiter/signup'
      assert.equal(request.url, expected); assert.equal(request.data.college_id,2)
      assert(!('role' in request.data)); assert.equal(roleHome(result.user.role),'/admin')
      if (expected==='/auth/recruiter/signup') assert.deepEqual(request.data.company,{name:form.name,industry:form.industry})
      if (expected==='/auth/signup') assert.equal(request.data.name,form.name)
    })
  }
  console.log(`${passed} navigation checks passed. Component rendering/request wiring only; no browser-interaction claim.`)
} finally { await server.close() }
