# Completion and acceptance ledger

Implementation work authorised on October 5, 2026 follows the KT audit. This ledger distinguishes code, local regression, deployment and owner acceptance. A UI or saved setting is not evidence of a successful live workflow.

## Existing implemented capabilities

Student/recruiter/admin authentication, email verification and college approval; JWT session revocation; password recovery and persisted rate limits; owned profiles/resume extraction; explained weighted readiness, matching, skill gaps and rule-based support; student-consented applications; recruiter review; availability/exam/working-hour constraints and interview rounds; conflict rechecking; targeted announcements and read receipts; distinct offer lifecycle stages; private PDF upload/download and human review; post-selection funnel and reasons; external assessment provenance; synthetic fairness/counterfactual report; privacy, owned export and restriction requests; regression CI and health monitoring.

These capabilities retain tenant application filters and all 34 ENABLE/FORCE RLS policies. Historical public job references and separately trained public-data placement experiments remain distinct from live campus vacancies and weighted rules.

## October 5 implementation additions

| Capability | Implementation |
| --- | --- |
| Placement-officer matching authority | College-scoped drive matching, original score preserved, promote/reject reason and actor role recorded. |
| Application-to-scheduling handoff | Admin review of consenting applications; explicit shortlist instruction. Matching never creates an application on a student's behalf. |
| Complete human profile review | Internship/employment/volunteering evidence saved on the student tenant row. Current profile/resume available only to authorised reviewers of an active application. Withdrawal/rejection removes this grant. |
| Reviewed job descriptions | Full description saved on each drive. Bounded vocabulary extraction requires human selection and target review. Optional or negated mentions are not automatically requirements. |
| Staff student directory | Paginated, college-scoped name/email search and profile/readiness review. Recruiter profile access requires an active consented application; closed applications deny current-profile reads. |
| Lexical NLP evidence | Separate pair-fitted TF-IDF comparison includes skills, projects, certificates, experience and resume text. Shared-term contributions and an explanation reconcile its score. It does not change eligibility, weighted score or ranking. No embedding/LLM/semantic-quality claim. |
| Governed drive closure | Owning recruiter or college admin closes/reopens with optimistic version checks and actor/reason/time history. New applications, matching runs and new interview proposals are blocked while closed. Existing workflows/history survive. |
| Assessment adoption | Evidence-only default. Staff explicitly adopts active external results; latest assessment date, then ID wins. Same policy resolves readiness/matching/support inputs, showing source/scale/date/recorder. Withdrawal restores older evidence or self-report; original profile inputs remain saved. Matching/support snapshots require rerun. |
| Recorded demand | Recruiter sees only company drives in that college; admin sees college drives. Open-drive skill counts and distinct student-drive outcomes are descriptive, not forecasts. |
| Assessment-event scheduling | Persisted interview/assessment types share constraints and round ordering. Rescheduling preserves type. Assessment events cannot be hiring selections or satisfy the offer prerequisite; reviewed results are recorded separately. |
| Durable in-app reminders | Unique persisted event/bucket keys for upcoming 24-hour and one-hour windows. Student feed checks due events; admin can run a college sweep. Optional configured worker checks while API runs, pauses for migration and retries after failure. No guaranteed on-time delivery on a sleeping free service. |
| Upload/browser hardening | Resume body limit before multipart parsing, bounded parser slots and child resource/time bounds; frontend CSP, anti-frame, referrer and MIME headers. |
| Student erasure execution | Read-only plan by default. Explicit private approval manifest, expired restricted request, retention and shared-reference checks; atomic scoped erasure plus receipt. Recruiter/admin shared records require separate reviewed succession/retention decisions. No live erasure performed. |

## Operations already verified

Complete encrypted production archive and isolated local restore: 87,362 rows, 34 tables, 171 colleges, exact record/file-byte digest and policies verified. Preliminary import into the restricted Neon runtime database is also verified. Source remains Render, and this preliminary snapshot was not taken under a complete write pause. No claim of completed cutover.

## Remaining external acceptance and decisions

- Owner must confirm the actual recovery/verification email and fresh admin login; no inbox access or password should be shared.
- Signed-in live acceptance of publication/read receipt, private file review/download, analytics and assessment adoption is distinct from local tests/API checks.
- Owner must provide the college retention grounds/period and erasure authority before processing real requests. JSON/free-text mentions, shared audit references, hashed limiter retention and backup copies require the approved disposition. Database-only deletion does not certify all-copy erasure.
- Final Neon cutover requires an approved maintenance window, complete write pause, fresh current-schema archive/restore, destination reconciliation and private connection update. The existing populated preliminary destination must not be cleared without explicit approval.
- Actual failed-run alert receipt and owner-controlled off-site backup retrieval remain owner acceptance checks.
- Semantic matching remains conditional on an explicit upgrade. The default is the documented keyword/weighted rule; lexical TF-IDF evidence is not semantic understanding.
- Matching fairness and real-world scoring accuracy cannot be established from synthetic cohorts. The written counterfactual/subgroup report documents limitations; real representative outcomes require a consented evaluation programme.
- Dedicated hosted/proctored exams, guaranteed on-time reminders, real hiring email/SMS, autoscaling and paid uptime are not claimed. Assessment results are recorded from external exams; their events share calendar constraints and named rounds. The reminder worker needs the explicit REMINDER_COLLEGE_IDS configuration for unattended sweeps; feed/admin checks work without it.

## Release evidence

Final full local regression: 200/200 cases pass in 521.040 seconds. The new completion-interface SSR checks and final production build pass. Earlier focused checks were separate runs, not additional distinct cases. PDF saturation is checked separately; concurrent upload tests honour Retry-After before verifying idempotency/version protection. Existing frontend checks passed earlier in this session. Build reports large bundle/logo assets; no load-time benchmark or uptime guarantee is claimed. Deployment and remote CI status will be recorded only after observation.

Implementation 9e2e0aa is deployed on Render (dep-db1os45g1s2s739t7pmg) and Vercel. All 41 public release checks pass, including API 0.19.0, all 34 policies, anonymous denial and served browser headers. The first remote CI run exposed a fresh-install JSON-default declaration error before regression; corrected using a SQL expression and verified on a new isolated local database. Remote rerun evidence is still pending; no authenticated live acceptance is inferred.
