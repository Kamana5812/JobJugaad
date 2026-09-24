# JobJugaad — Architecture Document

Reference implementation architecture for the JobJugaad platform. See `PRD.md` for requirements and `PHASES.md` for build order.

---

## 1. High-Level System Diagram

```
                        ┌─────────────────────┐
                        │   React Frontend     │
                        │   (Vercel)           │
                        │  /student /recruiter │
                        │  /admin              │
                        └──────────┬───────────┘
                                   │ REST (HTTPS, JSON)
                                   ▼
                        ┌─────────────────────┐
                        │   FastAPI Backend    │
                        │   (Render)           │
                        │  Auth · Routers ·    │
                        │  Rule Engines        │
                        └──────────┬───────────┘
                                   │ SQLAlchemy
                                   ▼
                        ┌─────────────────────┐
                        │  PostgreSQL          │
                        │  (Render Managed DB) │
                        │  + Row-Level Security│
                        └─────────────────────┘
```

---

## 2. Tech Stack

### Frontend
| Layer | Technology |
|---|---|
| Framework | React (Vite) |
| Language | JavaScript or TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Routing | React Router |
| HTTP client | Axios |

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Server | Uvicorn |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Auth | JWT (python-jose) + passlib (password hashing) |
| Resume parsing | pdfplumber / PyMuPDF, optionally LLM-assisted for free-text section extraction only (see §5, Profile AI) — this is the one place in the pipeline an LLM is justified |
| ML — **public-data placement signal** | pandas + scikit-learn RandomForestClassifier + joblib for the separate public-data placement signal; separate from weighted readiness; user-authorized integration |
| ML — **P2, conditional** | sentence-transformers (semantic matching) — do not install until the P1 rule-based Matching Engine works end-to-end |

### Database
| Layer | Technology |
|---|---|
| Primary DB | PostgreSQL |
| Vector search — **P1/P2, conditional** | pgvector — **not core stack.** Per `TECHNICAL_VALIDATION.md` Phase 16, add this only if semantic matching is actually attempted; installing it for a feature that stays rule-based all hackathon is unnecessary operational complexity |
| Row-level isolation | PostgreSQL Row-Level Security (RLS) policy on every multi-tenant table — see §8 Security |

### Deployment
| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend API | Render (Web Service) |
| Database | Render (Managed PostgreSQL) |

---

## 3. Folder Structure

```
jobjugaad/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── student/        (profile, readiness, skills, opportunities, applications)
│   │   │   ├── recruiter/      (company, drives, candidates, matching, schedule, offers)
│   │   │   └── admin/          (overview, students, drives, at-risk, analytics, simulator)
│   │   ├── components/         (shared UI: cards, tables, charts, pills)
│   │   ├── api/                (axios instance + endpoint wrappers)
│   │   ├── context/             (auth context, role context)
│   │   └── App.jsx
│   ├── .env                    (VITE_API_URL)
│   └── package.json
│
├── backend/
│   ├── main.py                 (app entrypoint, CORS, router registration)
│   ├── database.py             (engine, session, Base)
│   ├── models.py               (SQLAlchemy models — see §4)
│   ├── schemas.py              (Pydantic request/response schemas)
│   ├── auth.py                 (JWT creation/verification, password hashing)
│   ├── engines/
│   │   ├── readiness.py        (Readiness Score calculation)
│   │   ├── skill_gap.py        (Skill Gap Engine)
│   │   ├── matching.py         (Explainable Matching Engine)
│   │   ├── scheduler.py        (Conflict detection)
│   │   ├── risk.py             (At-Risk prediction)
│   │   └── simulator.py        (Jugaad Simulator — P2)
│   ├── routers/
│   │   ├── auth.py
│   │   ├── students.py
│   │   ├── recruiters.py
│   │   └── admin.py
│   ├── seed.py                 (synthetic dataset generator)
│   └── requirements.txt
│
├── PRD.md
├── ARCHITECTURE.md
├── RULES.md
├── PHASES.md
├── DESIGN.md
└── MEMORY.md
```

---

## 4. Database Schema

### Core Entities (conceptual roadmap; implemented inventory follows)
```
users, students, recruiters, companies
skills, student_skills, projects, certifications, assessments
jobs, matches
drives, schedules, applications, interviews
offers, documents
notifications
risk_predictions, simulations
```

**Implemented tenant tables (19):** users, students, student_skills, projects, certifications, companies, jobs, matches, match_overrides, schedules, interviews, schedule_events, risk_predictions, support_reviews, offers, offer_events, notifications, placement_model_profiles, btech_model_profiles. All include college_id. Jobs represent drives; several conceptual entities above have no separate table.

### Key Tables (fields)

**users**
`id, email, password_hash, role (student|recruiter|admin), college_id, created_at`

**students**
`id, user_id, name, branch, cgpa, backlog_count, resume_text, aptitude_score, communication_score, interview_score, readiness_score, college_id`

**student_skills**
`id, student_id, skill_name, proficiency (0–100)`

**projects / certifications**
`id, student_id, title, description`

**companies**
`id, recruiter_user_id, name, industry`

**jobs (drives)**
`id, company_id, title, ctc, min_cgpa, eligible_branches[], required_skills[], created_at, college_id`

**matches**
`id, job_id, student_id, match_score, factor_breakdown (JSON), missing_requirements (JSON), created_at`

**schedules / interviews**
`id, job_id, student_id, scheduled_time, venue, panel_id, status (upcoming|scheduled|completed|selected|rejected|pending)`

**Phase 3 implemented scheduling extensions:** `schedules` stores requested/proposed start, end, venue/panel, conflicts JSON, explanation, pending/scheduled/rejected status, source interview for rescheduling, creator/reviewer/reason, version and timestamps. `interviews` stores confirmed start/end, scheduled/completed/selected/rejected/cancelled status, optional schedule reference and unique seed key. `schedule_events` stores actor, action, reason and before/after snapshots. Composite tenant foreign keys bind every relationship to its college. All three tables have application filters and ENABLE/FORCE RLS from the same schema transaction.

**offers**
`id, student_id, job_id, ctc, offer_letter_status, documents_status, verification_status, acceptance_status, joining_status`

**risk_predictions**
`id, student_id, support_priority (low|medium|high), score, contributing_factors (JSON), recommendation (JSON)`

**Phase 3 implemented support extensions:** `risk_predictions` is unique per college/student/target job and stores the rule count (0–3), low/high support priority, flagged/assessable state, full factors/recommendations/explanation, evidence hash, evaluation time and active/reviewed/dismissed status. `support_reviews` stores the actor, action, reason and explained evidence snapshot. Both tables have college filters, composite tenant foreign keys and ENABLE/FORCE RLS. The historical table name does not imply a trained risk predictor.

### Phase 4 offer lifecycle and notifications

`offers` includes tenant/student/job/interview references, CTC, five separate stage fields, version, synthetic marker, optional seed key and timestamps. `offer_events` records actor (null only for synthetic imports), action, reason and before/after stage snapshots. `notifications` records tenant, recipient, deduplication event key, kind, title, body, target path, read time and creation time. All three tables receive ENABLE/FORCE RLS atomically with schema creation; every application query retains college filters. Composite foreign keys prevent cross-college references. Recipient/ownership checks additionally restrict access within a college.

Administrators create draft offers only after a selected interview, issue or withdraw letters, request document corrections, record verification and record joining. Only the owning student submits their document-status declaration or accepts/declines. Versions and row locks reject concurrent stale actions. Joining requires issued letter + student acceptance + verified submitted documents. Declined, withdrawn and joined/non-joined offers are closed. Every successful action adds an audit event and a simulated in-app notification in the same transaction; no email/SMS is sent. Student responses also notify college administrators.

This prototype tracks declarations about documents exchanged through the college's external channel. It does not store offer-letter/document files, perform automatic document validation or track post-joining careers. Notification reads are idempotent and recipient-scoped. Offer lists and eligible-interview choices are paginated; the calendar contains all scheduled bookings and the latest 50 other records. Matching and support persistence uses batches without changing formulas or discarding human reviews/overrides.

### Relationships
```
STUDENT ──< Skills
STUDENT ──< Projects
STUDENT ──< Certifications
STUDENT ──< Applications ──> Job
STUDENT ──< Interviews
STUDENT ──< Offers

RECRUITER ──> COMPANY ──< JOBS ──< MATCHES ──> STUDENTS
```

**Multi-tenancy:** every core table carries `college_id` so one deployment can serve multiple colleges; all queries filter by it.

---

## 5. Explainable Engine Architecture

The architecture separates seven responsibilities. The placement workflow uses rules plus a separate public-data placement classifier. The user reviewed metrics and authorized its integration on 2026-09-24; other model extensions still require explicit authorization. Each layer uses the simplest technique that satisfies the requirement, and every layer that produces a judgment about a student ends in human review, not an autonomous decision.

### Layer 1 — Rule Engine
Implemented hard constraints are branch eligibility, minimum CGPA and maximum backlog count. They run before shortlist ranking; the score cannot override them. Graduation-year filtering is not collected in this prototype. A separately logged human override may change shortlist status without changing the calculation.

### Layer 2 — Profile extraction (current) and optional future NLP

Current: PDF → pdfplumber text extraction → stored resume text for review. Students manually enter skills, projects, academics and existing assessments; recruiters enter structured requirements. Uploading text does not infer skills or change readiness. No LLM, embeddings, JD extractor or skill graph is implemented. Free-text section extraction is a separately authorized future option.

### Readiness Engine (feeds Layer 5)
```
Readiness Score = 30% Technical Skills + 20% Projects + 15% Academics
                + 15% Aptitude + 10% Communication + 10% Interview
```
Maps to official bands: `0–40 Not Ready · 41–65 Developing · 66–85 Ready · 86–100 Highly Employable`

The six-factor calculation is a proposed weighted rule over self-reported evidence, not a trained model or validated placement prediction. The weights and normalization require real outcome data before predictive-validity claims. Any future trained upgrade needs an appropriate dataset, independent evaluation and explicit authorization. No external research result is this prototype's performance.


#### Phase 1 normalization decisions (2026-09-22)

The six weights above are unchanged. Since the source formula does not prescribe component normalization, this implementation uses mean recorded skill proficiency, 25 points per recorded project capped at 100, CGPA x 10, and existing self-reported assessment scores on the 0-100 scale. Project count is a simple proxy, not a quality assessment. Missing factors contribute zero and are explicitly marked missing. Values and contributions are rounded half-up to two decimals; summed contributions are rounded half-up to a whole number before official band mapping. Every response includes score, raw total, six contributions with evidence, band, explanation, methodology, and a next step.

This is a proposed weighted rule with unvalidated normalization assumptions. Resume extraction stores text for human review; it does not infer skills, assign proficiency, or change readiness automatically. Certifications and backlogs are retained without adding factors to the fixed formula. This weighted rule introduces no trained model or new assessment/interview feature; the separately authorized public-data model is documented below.
### Layer 3 — Matching / Ranking Engine
```
Eligible Candidates (from Layer 1) → Skill Matching (keyword/weighted,
P0) → [P1/P2: Embedding Similarity via sentence-transformers + pgvector]
→ Weighted Ranking → Fit/Match Score
```
**Validated methodology (`TECHNICAL_VALIDATION.md` Phase 12):**
- **Normalization:** every component (CGPA, skill overlap %, assessment score, etc.) is scaled to a common 0–100 range before weighting, so no single component silently dominates the sum due to differing units.
- **Weighting:** starting weights (e.g. 32/24/15/12/8/5 across skill compatibility, project relevance, academic eligibility, assessment performance, experience, certifications) are **explicitly unvalidated starting assumptions**, not empirically derived — state this honestly rather than implying they were tuned against real data.
- **Threshold:** a minimum eligible score (e.g. 60/100) below which a candidate is excluded from the primary shortlist, with the reason surfaced via Layer 4.
- **Ranking:** simple descending sort on final score — no additional algorithm needed at hackathon scale.
- **Confidence:** do not report a numeric confidence score at P0 — there is no calibration data to justify one.
- **Evaluation:** define, don't fabricate — report precision/recall for the Matching Engine against a small, self-labeled synthetic ground truth (e.g. 10 profiles where you manually decide the "expected" top-3 matches), explicitly caveated as a synthetic sanity check, not a real-world accuracy claim.

The rule engine (Layer 1) decides *who is eligible*; this layer only *ranks who is already eligible* — weighted scores do not bypass eligibility rules.

#### Phase 2 matching decisions (2026-09-22)

- Proposed default weights: skill compatibility 40%, project relevance 20%, academics 20%, assessments 15%, certifications 5%. These total 100% and are configurable per drive. They are unvalidated starting assumptions, not empirical tuning; the illustrative weights above are examples, not fixed requirements. Experience is omitted because no structured experience field is collected.
- Normalize skills as the mean of capped proficiency / role-target ratios times 100; normalize project relevance as the percentage of required exact keywords appearing in project titles/descriptions. Case is ignored and word boundaries prevent Java matching JavaScript. No embeddings or LLM calls.
- Academics use CGPA x 10; assessments use the mean of the three existing /100 fields with absent fields contributing zero; certifications use 25 points per record, capped at 100, as an explicitly unvalidated count proxy. Missing evidence is identified. Values and contributions round half-up to two decimals; their sum is the thresholded score.
- Minimum CGPA, exact normalized branch and maximum backlog count are checked first. They cannot be overridden by a calculated score. Skill proficiency targets contribute to the weighted score; they are not additional hard eligibility rules. The default minimum match score is 60/100. Assessment benchmark defaults to 60 and is a review flag, not another hard rule.
- Only candidates passing hard eligibility and score threshold enter the primary shortlist. Excluded candidates retain diagnostic scores and factors for human review. Lists use descending score with student ID as a stable tie-breaker; no numeric confidence is returned.
- Excluded candidates with a real skill gap use the user-required fixed "Below Threshold: The student's [reason], but the required skill set shows a gap in [skill] and [other factor]." template. The user explicitly approved a truthful fixed no-skill-gap variant when all skill targets are met. Every result also includes missing requirements and an actionable next step.
- Skill-gap status is on-track at or above the role target, critical below half the target, and gap otherwise. Missing skill evidence is zero. These cutoffs are proposed assumptions; proficiency remains self-reported.
- Recruiter signup creates a user and company atomically. Recruiters see their own company's drives and candidate snapshots within their selected demo college. The four new tables (companies, jobs, matches, match_overrides) receive ENABLE/FORCE RLS in the same transaction as table creation; application queries and updates also carry college filters, alongside composite tenant foreign keys.
- Promote/reject is a human shortlist override, not a score modification. Audit rows retain reviewer, timestamp, reason, previous decision, and the full score/evidence snapshot. Reruns preserve manual decisions. Audit records have no edit/delete API; database-owner tamper resistance is not claimed.
- Demo data is generated in seed.py: 300 deterministic synthetic students, 12 synthetic companies, and three simulated drives. Existing profiles are preserved; unshared random passwords prevent public login to seed accounts. Startup runs a seeded drive only when it has no saved matches. Synthetic outputs do not establish real-world accuracy.

### Separate Placement Likelihood Model (public-data integration)

The public-data classifier predicts `Placed` / `Not Placed` from five academic/test percentages and seven categorical academic/work-experience fields, including gender and MBA specialisation. It is distinct from the unchanged six-factor weighted readiness formula. The CSV has no skills, projects, certifications or resume text, so it cannot validate those engines. Dataset provenance: [data notes](backend/data/README.md); frozen split/model/preprocessing choices: [training protocol](backend/ml/training_protocol.json). A Random Forest is used as requested; no unverified paper citation or claim of superiority to other trained models is asserted.

The 80/20 stratified split happens before fitting a one-hot encoder; class weights use training labels only. Salary and status are outcomes and sl_no is an identifier, all excluded from features. The persisted pipeline is trained on 172 records, tested on 43, with no holdout refit. The signal carries all 12 local contributing factors, a training-root baseline and a fixed explanation. It identifies uncalibrated model output and requires compatible recorded fields; missing MBA fields or degree percentages are not fabricated. The API loads the checksum-verified trusted artifact once per process at startup using pinned library versions, never retraining per request. A failed load disables only the model signal, with its status reported by /health. The existing At-Risk/support engine is unchanged and remains simple rules.

### Layer 4 — Explanation Engine
Every score from Layer 3 passes through a template-based explanation generator before reaching a student or recruiter — never a bare score. It states matching factors, missing requirements, and evidence drawn from the profile, in the format the problem statement requires:

> "Below Threshold: The student's CGPA meets the eligibility criteria, but the required skill set shows a gap in cloud technologies and the mock-interview score is below the recruiter's expected benchmark."

**Why template-based, never an LLM call:** an LLM here could hallucinate an incorrect reason, which would be actively more harmful to trust than no explanation at all. This is the single most important place in the whole pipeline to avoid LLM use.

### Layer 5 — Predictive Analytics (Placement Support Indicators)
```
Historical/Synthetic Data → Feature Engineering (skill gaps, mock
interview score, drive participation, application activity) →
Rule-based thresholds (P0) OR scikit-learn classifier with
class-imbalance handling (P1) → Support Priority + Contributing Factors
```
**Responsible framing:** this layer never predicts who will "fail" or "succeed." It identifies students who may benefit from additional placement support, based on measurable indicators (low readiness, skill gaps, low mock-interview performance, low activity) — output is a support-priority level and named contributing factors, not a pass/fail verdict.

**Critical methodological requirement if upgraded to a classifier:** inspect class balance and handle imbalance with SMOTE or class weighting inside an appropriate training/evaluation split. Remind the user of this prerequisite if an upgrade request omits it. No classifier or trained accuracy result exists in this release.

**Phase 3 rule, explicitly unvalidated:** flag only when all three conditions hold: (1) at least three required role skills have gap/critical status, (2) the existing self-reported interview score is known and below 40/100, and (3) fewer than two completed interview records exist in the past 30 days. Completed includes completed/selected/rejected, excludes cancelled/future interviews, and uses end time. Missing interview scores remain unknown and cannot trigger the combined flag. Recorded activity is an opportunity/record proxy, never a measure of effort.

The score is the count of triggered conditions out of three, **not a probability or confidence**. Every returned score includes all named factors, observed values, thresholds, contributions and explanation; flagged records add technical practice, mentor-led interview preparation and opportunity/attendance review. No automated mock interview is built. Admins may mark reviewed, dismiss or reopen with a reason. Recalculation preserves reviews only while the evidence hash stays identical; changed evidence requires fresh review. Recommendations and flags do not initiate interventions automatically. Remind the user about SMOTE/class weighting if a future classifier request omits it.

### Layer 6 — Intervention Engine
```
Support Priority + Contributing Factors → Rule-Based Recommendation
Lookup → Suggested Actions (training / mentoring / mock interview) →
[Planned: Reassessment After Action → Before/After Readiness Delta]
```
Converts a Layer 5 indicator into a specific, actionable recommendation — never a bare label. This is a lookup/mapping task, not a prediction task. The before/after tracking loop (re-running the Readiness Engine after a suggested action to measure change) is the target design; if not implemented in the P0/P1 build, it must be described as a **planned capability**, not a working feature.

### Layer 7 — Human Oversight
Recruiters may promote/reject candidates for their own drives with audited reasons. Administrators approve/reject scheduling proposals and review/dismiss support suggestions; students edit their own profile evidence. These role-specific actions do not imply that every role can edit every field. No irreversible placement decision is made automatically.

### Scheduling Engine (cross-cutting, works alongside Layers 1–7)
```
New Interview Request → Check Student Availability → Check Venue →
Check Panel → Check Overlapping Drives → Conflict? → Propose Next
Free Slot → Layer 7 Approval → Confirm
```
Implemented as a **deterministic greedy constraint-checker**, with no LLM or metaheuristic solver. It proposes the next slot clearing recorded student, venue and panel conflicts within its bounded search. No globally optimal timetable is claimed. Each proposed resolution requires administrator approval and a fresh conflict check.

**Phase 3 scheduling mechanics:** all stored times include UTC offsets; forms display the browser timezone. Intervals are half-open, so adjacent interviews do not conflict. Resource names are normalized for case/whitespace. Different drives may overlap only when they share no student, venue or panel; a shared-resource clash on another drive is explicitly explained as overlapping drives. The deterministic greedy search jumps to the latest end of the current blockers and repeats, bounded to seven days. Working hours and panel qualifications are not modeled; an administrator reviews the proposed time.

Pending proposals do not reserve resources. A college-scoped PostgreSQL transaction advisory lock serializes confirmation/rescheduling/status changes; approval checks current availability again. Stale versions or newly occupied slots return 409 for recheck. Rescheduling cancels the old interview and inserts the replacement atomically only after approval, retaining history and audit evidence. Outcomes cannot be recorded before the interview ends. The seed deliberately imports two overlapping synthetic bookings; normal API confirmation cannot introduce that overlap. Seed keys preserve resolved fixtures across restarts.

**Phase 3 analytics:** branch/skill conversion is distinct students shortlisted for any drive divided by recorded students in that group. It uses saved match snapshots and human overrides; it is not offer/placement conversion. Advertised CTC min/mean/max come from jobs. Phase 4 adds an accepted-offer placement proxy: distinct students with an issued, accepted offer not marked not joined / recorded students. Joining is counted separately; synthetic offers are included and explicitly labeled. Advertised CTC remains per drive, while accepted CTC is per qualifying offer, so multiple offers for one student count separately in package statistics. No fabricated outcomes or benchmark metrics appear.

### Simulator (P2)
```
Admin Input (e.g. "train 200 students in AWS") → Adjust Synthetic
Skill Distribution → Recompute Eligibility → Apply Historical
Conversion Rate → Projected Eligible Students / Offers
```
Outputs are always labeled as projections generated from the synthetic dataset's own model — never presented as validated forecasts.

---

## 6. API Design (implemented representative endpoints)

The live `/openapi.json` is the exhaustive route/contract reference. These routes are implemented; student opportunities, automated JD extraction and simulator routes are not.

```text
POST /auth/signup
POST /auth/recruiter/signup
POST /auth/login
GET  /auth/me
GET  /students/{student_id}
PUT  /students/{student_id}
POST /students/{student_id}/resume
GET  /students/{student_id}/readiness
GET  /recruiters/company
PUT  /recruiters/company
GET  /recruiters/jobs
POST /recruiters/jobs
POST /recruiters/jobs/{job_id}/matching
GET  /recruiters/jobs/{job_id}/matches
POST /recruiters/jobs/{job_id}/matches/{match_id}/override
GET  /admin/analytics/overview
GET  /admin/schedules
POST /admin/schedules/check-conflict
POST /admin/schedules
POST /admin/schedules/{schedule_id}/review
POST /admin/schedules/{schedule_id}/recheck
PUT  /admin/interviews/{interview_id}/status
GET  /admin/support
POST /admin/support/run
POST /admin/support/{prediction_id}/review
GET  /admin/offers
GET  /admin/offers/eligible-interviews
POST /admin/offers
PUT  /admin/offers/{offer_id}
GET  /students/{student_id}/offers
POST /students/{student_id}/offers/{offer_id}/actions
GET  /notifications
PUT  /notifications/{notification_id}/read
GET  /health
```

All authenticated endpoints require a `Bearer <JWT>` header; the token payload includes `user_id`, `role`, and `college_id`.

---

## 7. Deployment Architecture

| Concern | Approach |
|---|---|
| Frontend hosting | Vercel, auto-deploy from `main` branch, root dir `frontend/` |
| Backend hosting | Render Web Service, auto-deploy from `main`, root dir `backend/` |
| Database | Render Managed PostgreSQL (free tier) |
| Env vars (frontend) | `VITE_API_URL` |
| Env vars (backend) | `DATABASE_URL`, `JWT_SECRET`, `ADMIN_ACCOUNTS` (explicit existing accounts) |
| CORS | Backend allows only the deployed Vercel origin in production |
| Cold starts | Render free tier sleeps after 15 min idle — warm up before demos |

---

## 8. Security

- Passwords hashed with `passlib` (bcrypt).
- JWT tokens carry role + college_id; every router checks role before returning data. Phase 3 admin access uses server-only `ADMIN_ACCOUNTS`, a JSON array of existing email/college pairs. Startup promotes only those accounts; no public signup can request admin. Every admin login/request checks both database role and the current allowlist. Removing the pair denies access even to an unexpired token. A missing configured account fails startup with a registration instruction; it never creates a default password. Log in again after promotion because old student/recruiter tokens no longer match the database role.
- **Two-layer multi-tenancy enforcement:** application-level `WHERE college_id = ...` filtering on every query, **plus** a PostgreSQL Row-Level Security (RLS) policy on every multi-tenant table as a database-enforced second layer. RLS scopes database reads and writes to the transaction's college. Student ownership, recruiter company ownership and administrator permissions within a college are separate application checks; college RLS alone does not isolate individual students within that college.
- CORS locked to the known frontend origin in production.
- No secrets committed to the repo — all via environment variables (see `RULES.md`).
- Least-privilege access throughout: each role reaches only the endpoints and data it needs; resumes, documents, and offer details are restricted to the owning student, the relevant recruiter, and admin.
- Audit-relevant actions (Layer 7 overrides, schedule changes, dismissed support flags) are logged for admin review.
- **No absolute security claims.** Never describe the system as "100% secure," "completely private," or "military-grade" — no system can honestly claim this. State what is actually implemented (JWT + RBAC + RLS + least-privilege access) and nothing beyond it.

---

## 9. Dataset & Evaluation

### Scalability & Deployment Approach

Every core table carries a `college_id` column enforced by both application-level filtering and a PostgreSQL Row-Level Security policy, so one deployment can serve multiple colleges as isolated tenants without re-architecture. FastAPI uses a transaction-local college context derived from authenticated identity, ENABLE/FORCE RLS with read/write predicates, role and ownership checks, and composite tenant foreign keys; the runtime role cannot bypass RLS. React is deployed on Vercel and FastAPI with managed PostgreSQL on Render. The demo exposes two self-selected colleges; real campus onboarding needs institution-controlled enrollment and tenant configuration, rather than a new data model. More traffic requires measured capacity planning, suitable database/service sizing and operational hardening; no production-scale benchmark is claimed.

| Category | Status |
|---|---|
| **Real/public labeled data** | Imported Campus Recruitment records, publisher-described anonymized campus data; collection not independently audited. Used to train the separate placement-status model exposed alongside weighted readiness. |
| **Public model training** | `backend/data/Placement_Data_Full_Class.csv`: 215 records, status labels; 172 training / 43 held-out test records. pandas + Random Forest + joblib; no salary or ID predictors. Student-owned academic inputs and an explained model signal are integrated separately from the weighted rule. |
| **Synthetic data** | ~4,800-student demo dataset (see `seed.py`) — for UI/scale demonstration only, never described as validating model accuracy |
| **Simulated workflow data** | Scheduling, offers and notifications in the demo are fictional. Jugaad Simulator is not implemented. |

**Evaluation protocol (do not skip, do not fabricate):**
- Matching Engine: precision/recall against a small, self-labeled synthetic ground truth — label clearly as a sanity check.
- Readiness Engine: face-validity review against manually inspected sample profiles.
- At-Risk classifier (if built past P0 rules): ROC/precision-recall evaluation with class-imbalance-aware methodology (SMOTE or class weighting) — never report raw accuracy alone on an imbalanced classification task.


### Phase 4 observed synthetic evaluation — 2026-09-23

The local dataset contains 4,800 synthetic students (4,796 numbered profiles plus four preserved support cases), 45 synthetic companies and 13 simulated role specifications. A shared noisy preparation factor correlates CGPA, skills, projects and assessments with fictional selection/outcome imports; random variation preserves exceptions. Earlier seed records and human changes are not overwritten. Synthetic offer records are explicitly marked; their counts are not observed placements or model predictions.

[EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) and `backend/evaluation_expected.json` were frozen in commit `c2748bf` before engine evaluation. Ten manually inspected profiles have assistant-authored expected top-three roles, readiness bands and support flags, with input hashes and written reasons. [The report](evaluations/phase4-report.md) records **25 of 30 expected matches reproduced**, synthetic precision 25/30 and recall 25/30, **10/10 readiness-band agreements** and **10/10 support-flag agreements**. All five missing expected matches and full evidence are retained in the report and companion JSON. No weights, profiles or labels were tuned after observing results.

These are synthetic sanity checks against our own assumptions and a face-validity review, not validated accuracy or independent human validation. The convenience sample lacks a Not Ready example and contains only one flagged support case. No generalization, calibrated confidence, latency benchmark or causal outcome claim follows. Requirement-coverage scoring may favor easier role targets over specialist fit. Re-running `backend/evaluate.py` refuses changed input/activity hashes rather than silently comparing different profiles; activity is time-sensitive and will age out of its 30-day window.

### Phase 5 deployment verification

`/health` checks actual PostgreSQL catalogs for all 19 modeled tables and unexpected tenant tables. It verifies college_id, ENABLE/FORCE RLS, the sole ALL-command college_isolation policy with matching USING/WITH CHECK predicates, and a non-superuser/non-BYPASSRLS runtime role. Schema initialization fails closed on policy drift; unhealthy checks return 503. The public report contains policy status only, never tenant records, role names or credentials. See [Phase 5 audit](PHASE5_AUDIT.md) and [demo guide](DEMO_GUIDE.md). Catalog checks complement cross-tenant integration tests and application ownership checks.

### Public-data placement classifier — measured evaluation (2026-09-24)

Accuracy **88.37%**, precision **93.10%**, recall **90.00%**, F1 **91.53%** (positive class: Placed; **43 held-out records**, 172 training, 215 total). Confusion matrix (actual rows / predicted columns, order Not Placed, Placed): `[[11, 2], [3, 27]]`. Majority-class baseline accuracy is 69.77%. These are measured results on imported public labels, not synthetic expected labels. The fixed stratified split and parameters were committed before training; no test-set tuning or refit was performed. See [full measured report](backend/ml/evaluation_report.json), [readable evaluation](backend/ml/EVALUATION.md) and [dataset provenance](backend/data/README.md).

User authorized API/frontend integration after reviewing these metrics on 2026-09-24; the public dataset is not required to originate from BPUT. Its 215-record source and 43-case holdout do not establish external validity for BPUT or calibrated individual likelihoods. The saved model was fitted on 172 records; do not imply all 215 were used for training. No skills/project/certification/resume labels exist in this public dataset. Existing weighted readiness and rule-based support remain unchanged, and Phase 4 matching/readiness/support evaluations retain their synthetic sanity-check framing. Inference loads the trusted pipeline once at startup, collects optional compatible fields and returns distinct explained outputs. GET/PUT /students/{student_id}/placement-model uses JWT ownership, college_id filters and ENABLE/FORCE RLS on placement_model_profiles. The new one-to-one table has a composite student/college foreign key; no existing rows or seed outcomes are rewritten. Its inputs JSON contains only the 12 validated predictors. Per-tree parent-to-child changes in the Placed score are averaged and aggregated across one-hot columns into original fields; baseline plus signed contributions exactly reconstructs the forest output. This is model-path attribution, not causality or SHAP.

### Optional academic-input persistence

`placement_model_profiles`: id, college_id, student_id, inputs (JSON with exactly the 12 validated model fields; nullable values retained), updated_at. Unique (student_id, college_id), composite foreign key to students(id, college_id). Application college filters, student ownership and the same ENABLE/FORCE college_isolation policy apply. This additive table is created in the schema/RLS transaction before serving; it does not alter or backfill existing student fields. The immutable public CSV and trained model are non-tenant artifacts, not student accounts.

### BTech / BE public-data placement extension — 2026-09-24

User authorized a BTech-specific model alongside the existing MBA signal. Source is Tejashvi/Kaggle Engineering Placements Prediction version 6 (CC0), with publisher-reported 2013–2014 university records; original collection is not independently audited. The BTech artifact uses semester-6 CGPA, stream, internships and ever-backlog history. Exclude Age, Gender, Hostel and the target from predictors; this is a predeclared design choice, not a fairness result. Preserve the MBA and six-factor weighted-readiness outputs unchanged.

Dataset 2,966 rows / 181 distinct modeled profiles. First fixed five-fold StratifiedGroupKFold split (shuffle true, seed 42): train 2,374 rows / 140 groups, test 592 rows / 41 groups; identical modeled inputs never cross splits. One 300-tree balanced-class Random Forest, train-only encoding, no test tuning or holdout refit. Accuracy 83.95%, Placed precision 96.77%, recall 73.39%, F1 83.48%; matrix [[257,8],[87,240]] (actual rows/predicted columns [Not Placed,Placed]). Majority baseline 55.24%. [Full evaluation](backend/ml/engineering/EVALUATION.md). The 87 missed placed records and older repeated-input dataset limit interpretation; this is not calibrated individual likelihood or current-college validation.

`btech_model_profiles`: id, college_id, student_id, inputs JSON (four optional validated fields), updated_at; unique (student_id,college_id), composite foreign key to students(id,college_id). Created atomically with ENABLE/FORCE college_isolation RLS; GET/PUT /students/{student_id}/btech-placement-model also enforce ownership and explicit college filters. Total tenant tables: 19. Six source streams only; CGPA outside 5–9 or internships above 3 yield no model score, preserving submitted evidence. Backlog history is collected explicitly rather than inferred from active backlogs. Trusted checksum/version-checked artifact loads once per process; /health reports btech_model separately from the MBA placement_model status. Both use a shared exact original-field tree-path attribution helper; a score is returned only with its baseline, full factors and fixed explanation. No new packages or automatic recruitment decisions.
