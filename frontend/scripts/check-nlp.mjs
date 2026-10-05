import assert from 'node:assert/strict'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
const server = await createServer({ root: fileURLToPath(new URL('../', import.meta.url)), server: { middlewareMode: true, hmr: false }, appType: 'custom' })
try {
  const Semantic = (await server.ssrLoadModule('/src/components/SemanticComparison.jsx')).default
  const Resume = (await server.ssrLoadModule('/src/components/ResumeSuggestions.jsx')).default
  const semantic = renderToStaticMarkup(React.createElement(Semantic, { studentId: 1, jobId: 2 }))
  assert.match(semantic, /pretrained sentence-embedding model/)
  assert.match(semantic, /does not alter eligibility/)
  assert.match(semantic, /Compare semantic evidence/)
  const resume = renderToStaticMarkup(React.createElement(Resume, { profile: { id: 1, resume_text: 'Recorded text' } }))
  assert.match(resume, /Nothing is selected or saved automatically/)
  assert.match(resume, /Skill mentions do not establish proficiency/)
  assert.match(resume, /Preview extracted fields/)
  console.log('PASS NLP initial-state rendering: local model disclosure, ranking separation and review-only resume suggestions. No browser or model accuracy claim.')
} finally { await server.close() }
