import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
const root=fileURLToPath(new URL('../',import.meta.url))
const data=JSON.parse(readFileSync(new URL('../../.local/dashboard-render-data.json',import.meta.url),'utf8'))
const server=await createServer({root,server:{middlewareMode:true},appType:'custom'})
const h=React.createElement
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;')
const render=(C,props)=>renderToStaticMarkup(h(C,props))
let passed=0
const check=(name,fn)=>{fn();passed++;console.log('PASS '+name)}
try {
 const Hero=(await server.ssrLoadModule('/src/components/PortalHero.jsx')).default
 const Ready=(await server.ssrLoadModule('/src/components/ReadinessCard.jsx')).default
 const Opportunity=(await server.ssrLoadModule('/src/pages/student/OpportunityCard.jsx')).default
 const {OpportunitiesContent}=await server.ssrLoadModule('/src/pages/student/OpportunitiesPanel.jsx')
 const Gaps=(await server.ssrLoadModule('/src/pages/student/SkillGapTable.jsx')).default
 const Candidate=(await server.ssrLoadModule('/src/pages/recruiter/CandidateCard.jsx')).default
 const Support=(await server.ssrLoadModule('/src/pages/admin/SupportCard.jsx')).default
 const Analytics=(await server.ssrLoadModule('/src/pages/admin/AnalyticsPanel.jsx')).default
 const Attention=(await server.ssrLoadModule('/src/pages/admin/AdminAttention.jsx')).default
 for (const role of ['student','recruiter','admin']) check(role+' hero uses its own imported illustration and role identity',()=>{
   const html=render(Hero,{role,collegeId:1})
   assert(html.includes(`/src/assets/hero/${role}.png`));assert(html.includes('Demo College'))
   assert(html.includes('People make the final decisions'));assert(!html.includes('AI-powered'))
 })
 check('readiness still renders all six factors and explanation',()=>{
   const r=data.profile.readiness,html=render(Ready,{readiness:r,dirty:true})
   assert(html.includes(esc(r.explanation))&&html.includes('Unsaved changes'))
   for(const f of r.breakdown)assert(html.includes(esc(f.label))&&html.includes(esc(f.evidence)))
 })
 for(const o of [...data.opportunities.items,data.opportunities.target]) check('opportunity '+o.job_id+' has complete score evidence',()=>{
   const html=render(Opportunity,{opportunity:o,position:1})
   assert(html.includes(esc(o.explanation))&&html.includes(esc(o.next_step))&&html.includes(esc(o.methodology)))
   for(const f of o.factor_breakdown)assert(html.includes(esc(f.label))&&html.includes(esc(f.evidence)))
   for(const gap of o.missing_requirements)assert(html.includes(esc(gap)))
   assert(html.includes('not a recruiter decision'))
 })
 check('skill comparison shows named statuses, targets, explanation and next steps',()=>{
   const gaps=data.opportunities.target.skill_gaps,html=render(Gaps,{gaps})
   for(const g of gaps)assert(html.includes(esc(g.skill_name))&&html.includes(esc(g.explanation))&&html.includes(esc(g.next_step)))
   assert(html.includes('Target /100')&&html.includes('Recorded /100'))
 })
 check('student full and empty states are explicit and preserve dirty warning',()=>{
   const handlers={onStatus(){},onTarget(){},onPage(){}}
   const html=render(OpportunitiesContent,{data:data.opportunities,status:'all',dirty:true,...handlers})
   assert(html.includes('Unsaved profile changes')&&html.includes('Kahan Kami Hai?')&&html.includes('Aapke Liye Sahi Jobs'))
   const empty={...data.opportunities,items:[],roles:[],target:null,total:0,eligible_count:0,excluded_count:0}
   assert(render(OpportunitiesContent,{data:empty,status:'eligible',...handlers}).includes('No drives have been recorded'))
 })
 for(const c of data.candidates)check('recruiter candidate '+c.id+' retains factor breakdown and human review',()=>{
   const html=render(Candidate,{candidate:c,position:1,onReviewed(){}})
   assert(html.includes(esc(c.explanation))&&html.includes('Human review'))
   for(const f of c.factor_breakdown)assert(html.includes(esc(f.label)))
 })
 for(const s of data.support.students.slice(0,5))check('support student '+s.student_id+' retains named indicators and interventions',()=>{
   const html=render(Support,{student:s,onReviewed(){}})
   assert(html.includes(esc(s.explanation))&&html.includes('Recommended support'))
   for(const f of s.contributing_factors)assert(html.includes(esc(f.label))&&html.includes(esc(f.explanation)))
 })
 check('admin overview retains KPI meaning, outcome distinction and current conflict explanations',()=>{
   const html=render(Analytics,{data:data.analytics,children:h(Attention,{board:data.board,onSection(){}})})
   assert(html.includes('Accepted-offer proxy')&&html.includes(esc(data.analytics.placement_explanation)))
   assert(html.includes('Recorded offer outcomes')&&html.includes('joining are distinct'))
   for(const c of data.board.conflicts.slice(0,3))assert(html.includes(esc(c.explanation)))
 })
 console.log(`${passed} dashboard rendering checks passed using actual database outputs; not a browser interaction test.`)
} finally {await server.close()}
