import assert from 'node:assert/strict'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const root = fileURLToPath(new URL('../', import.meta.url))
const server = await createServer({root, server:{middlewareMode:true, hmr:false}, appType:'custom'})
try {
  const Records = (await server.ssrLoadModule('/src/components/AssessmentRecords.jsx')).default
  const item = {id:42,student_id:17,student_name:'Controlled student',kind:'skill',skill_name:'Python',
    title:'External Python result',source:'Controlled provider',reference:'<script>alert(1)</script>',
    score:30,maximum:40,normalized_score:75,explanation:'Recorded 30 out of 40; score / maximum × 100 = 75/100. Staff declaration, not a readiness contribution.',
    assessed_on:'2026-10-03T09:00:00Z',created_at:'2026-10-04T09:00:00Z',recorded_by:8,reason:'Reviewed controlled source evidence.',
    withdrawn_at:null,withdrawn_by:null,withdrawal_reason:null}
  const render = props => renderToStaticMarkup(React.createElement(Records, props))
  const student = render({items:[item]})
  assert.match(student,/30 \/ 40/)
  assert.match(student,/score \/ maximum/)
  assert.match(student,/Controlled provider/)
  assert.match(student,/College administrator #8/)
  assert.match(student,/&lt;script&gt;/)
  assert.doesNotMatch(student,/<script>|Withdraw an incorrect/)
  const admin = render({items:[item],onWithdraw:()=>{},busy:false})
  assert.match(admin,/Withdraw an incorrect record/)
  const withdrawn = render({items:[{...item,withdrawn_at:'2026-10-04T10:00:00Z',withdrawn_by:8,withdrawal_reason:'Incorrect reference; original retained.'}],onWithdraw:()=>{}})
  assert.match(withdrawn,/Withdrawn · history retained/)
  assert.match(withdrawn,/Incorrect reference; original retained/)
  assert.doesNotMatch(withdrawn,/Withdraw an incorrect record/)
  const {api} = await server.ssrLoadModule('/src/api/client.js')
  const calls=[]
  api.defaults.adapter = async config => {calls.push(config);return {data:{items:[]},status:200,statusText:'OK',headers:{},config}}
  const wrapper=await server.ssrLoadModule('/src/api/assessments.js')
  await wrapper.getAssessments(17,{offset:20});await wrapper.getAssessments(null,{student_id:17})
  await wrapper.recordAssessment({student_id:17});await wrapper.withdrawAssessment(42,'Incorrect reference.')
  assert.deepEqual(calls.map(x=>[x.method,x.url]),[['get','/students/17/assessments'],['get','/admin/assessments'],['post','/admin/assessments'],['post','/admin/assessments/42/withdraw']])
  assert.equal(calls[0].params.offset,20)
  assert.equal(calls[1].params.student_id,17)
  console.log('PASS 13 assessment rendering and API transport assertions')
} finally {await server.close()}
