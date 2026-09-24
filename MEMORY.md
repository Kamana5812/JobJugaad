# JobJugaad — Project Memory

Living record of project state and decisions. Update this file whenever a major decision is made or a phase completes — this is the single source of truth for "where things stand," especially useful for onboarding teammates or resuming work with an AI coding assistant.

**Last updated:** 2026-09-24
**Current phase:** Landing/auth navigation preview on `feature/role-navigation`, awaiting user review before dashboard redesign. Production remains BTech / BE + MBA (API 0.8.0, application release bb3f743); all 19 tenant policies verified.

---

## 1. Project Identity

- **Name:** JobJugaad
- **Event:** BPUT Hackathon 2026, Problem Statement 10 (official title: "CampusLink — AI-Powered Campus-to-Corporate Placement Management & Analytics Platform")
- **Tagline:** "Placement ka Jugaad, AI ke Saath."
- **Repo:** https://github.com/Kamana5812/JobJugaad (public; initial commit `d39492c` pushed to `main` with explicit user approval)
- **Live URLs:** Frontend: https://jobjugaad.vercel.app · Backend health: https://jobjugaad-api.onrender.com/health

---

## 2. Key Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-09-24 | Unified `/auth` role-first flow; verified server role controls navigation | Reuse existing JWT endpoints and `/auth/me`; never create public admin signup. User explicitly requires landing/role-selector review before dashboard redesign |
| 2026-09-24 | Separate BTech / BE model using Tejashvi engineering placement data (CC0 v6), without MBA inputs | User requested BTech integration; 2013–2014 publisher-reported records with 181 distinct modeled profiles require a group-disjoint evaluation. Use four educational fields, exclude age/gender/hostel, retain human decisions and explain every score |
| 2026-09-24 | Integrate the public Campus Recruitment model; the source need not be BPUT data | User approved after seeing metrics. Optional 12-field academic profile, load-once trusted artifact, separate explained score, 18th RLS table; no automatic hiring decisions or changes to weighted readiness |
| — | Stack: React + Tailwind (frontend), FastAPI (backend), PostgreSQL (DB) | Free-tier deployable on Vercel + Render; matches team's existing React/JS skills |
| — | Rule-based scoring for MVP, not black-box ML | Problem statement explicitly requires explainability; rule-based is transparent and easy to justify to judges |
| — | Deployment target: Vercel (frontend) + Render (backend + DB) | Both have generous free tiers, GitHub auto-deploy, beginner-friendly |
| — | Synthetic dataset (~4,800 students, 40–50 companies), not real data | No real student/recruiter data available for a hackathon |
| — | Brand palette: Navy / Saffron / Green / White | Indian identity that feels modern, not like tricolor kitsch — see `DESIGN.md` |
| — | Readiness Score weighting: 30/20/15/15/10/10 (Technical/Projects/Academics/Aptitude/Communication/Interview) | Proposed implementation model — explicitly documented as not an official BPUT formula |
| — | Positioning reframed from "AI-powered" to "explainability-first" | Competitive/research review (`RESEARCH_AUDIT.md`) confirmed most of the system is deliberately rule-based, not ML — leading with "AI-powered" was vulnerable to the judge question "why is AI required?" |
| — | AI Mock Interview dropped from roadmap entirely; AI Career Chatbot demoted to static UI label only | 10+ mature dedicated competitors found for mock interview; a near-identical academic chatbot prototype (Campus-Connect) already exists — building either adds effort with zero differentiation (`TECHNICAL_VALIDATION.md` Phase 10) |
| — | Added PostgreSQL Row-Level Security as a second multi-tenancy enforcement layer beneath application-level `college_id` filtering | Confirmed as a real, implemented pattern via direct inspection of a comparable project (`codeecoffee/SmartCampus`) — stronger answer to "how is student privacy protected?" |
| — | Cited `Placement_Data_Full_Class.csv` (Kaggle) by name as the recommended real dataset anchor for Readiness Engine weight validation | Confirmed as the same dataset independently used across 5+ public student projects (`RESEARCH_AUDIT.md` Phase 6 addendum) |
| — | Jugaad Simulator repositioned as "applying an established workforce-planning technique to an underserved category," not an invention | "What-if scenario simulation" is a known HR analytics pattern (SAP/MiHCM); the innovation is the application to campus placement, not the technique itself |
| — | AI Architecture restructured from 4 engines into an explicit 7-layer model (Rule Engine → NLP/Embedding → Matching/Ranking → Explanation → Predictive Analytics → Intervention Engine → Human Oversight) | Aligns with the official CampusLink guidance on hybrid, explainable, human-overseen AI; makes clear the AI never independently makes an eligibility or placement decision |
| — | "At-Risk" renamed to "Placement Support Intelligence" throughout product materials; risk labels replaced with support-priority + contributing factors | Official guidance requires responsible language — "at-risk" must not imply failure; the system identifies students who may need support, not predicted outcomes |
| — | Added "Reject Less → Identify the Gap → Help the Student Improve" as the stated core product philosophy | Directly reflects the official CampusLink video guidance on how rejections/explanations should be framed |
| — | Placement Intervention Engine (before/after readiness tracking) documented as the target design, explicitly marked planned/future unless actually built | Avoids overclaiming a capability that may not exist in the working P0/P1 prototype |
| 2026-09-21 | Saved the supplied horizontal wordmark as `assets/logo_horizontal.png` and square JJ mark as `assets/logo_poster.png` | Uses the asset paths requested by the user; JPEG inputs converted to PNG without artwork changes. Horizontal wordmark is intended for the navbar, and the square mark for login/landing screens. |
| 2026-09-21 | Use JavaScript with React/Vite and the Tailwind Vite plugin | Matches the team's React/JS experience and the permitted architecture; installs the requested Axios, React Router, and Recharts packages without semantic-matching dependencies. |
| 2026-09-21 | Health response distinguishes an unconfigured database from a connected database; configured connection failures return HTTP 503 | Phase 0 must verify a real backend/database pipeline rather than display a misleading success. The SQLAlchemy SELECT 1 probe does not access tenant data. |
| 2026-09-21 | Prepare a Render Blueprint template; keep CORS open temporarily without credential support | The template supports fresh environments; the actual deployment reused an existing database through dashboard configuration. Restrict CORS in Phase 5. No multi-tenant tables are created before Phase 1. |
| 2026-09-21 | Reuse the existing public Kamana5812/JobJugaad repository | GitHub already has this name; preserve the user's existing repository and visibility rather than create a duplicate or change settings. |
| 2026-09-21 | Reuse the existing Render PostgreSQL instance `Job-Jugaad` in Oregon; configure the web service through Render's dashboard | The database was already available when account access completed. Its internal connection string is stored only in the backend service's `DATABASE_URL`, never in git or frontend variables. `render.yaml` remains a fresh-environment template, not the mechanism used for this deployment. |
| 2026-09-21 | Publish all committed files to the existing public repository following explicit user approval | Automatic approval review initially blocked public publication of the project documents; the user explicitly approved publishing code, logos, and documents, and the subsequent push succeeded. |

| 2026-09-22 | User accepted Phase 0 and explicitly authorized Phase 1 Student Core | Both Phase 0 live URLs are confirmed working; Phase 2 remains gated. |
| 2026-09-22 | Normalize readiness with mean skill proficiency, 25 points/project capped at 100, CGPA x 10, and existing assessments /100 | Source weights are fixed but normalization was unspecified; assumptions are explicit, self-reported, and unvalidated. Missing evidence is marked and contributes zero. |
| 2026-09-22 | Create all five tenant tables and FORCE RLS atomically; reject superuser/BYPASSRLS runtime roles | Prevent any serving window without database isolation; retain explicit application college filters, student ownership checks, and composite tenant foreign keys. |
| 2026-09-22 | Student-only signup into two self-selected demo colleges | No real institution enrollment verification is available; UI requires synthetic demo details and privileged roles cannot be submitted through signup. |
| 2026-09-22 | Use bcrypt via passlib with bcrypt 4.0.1, two-hour HS256 JWTs and tab-scoped sessionStorage | Pins a compatible bcrypt implementation, preserves 72-byte limits, checks signed identity claims, and provides a bounded MVP session. No refresh/reset/revocation feature is claimed. |
| 2026-09-22 | Keep resume extraction in a bounded subprocess and store text only | PDF limit 5 MB/20 pages/200,000 characters and 20-second parser deadline; no automatic skill or readiness inference. |
| 2026-09-22 | Seed 50 deterministic synthetic profiles idempotently at startup | Makes the requested test population available after deployment; unshared random passwords prevent public seed-account login. |
| 2026-09-22 | Use a workspace-local PostgreSQL binary for real RLS integration tests | Local test role has no bypass privileges; tooling/data/credentials remain ignored in .local/ and are not application dependencies. |
| 2026-09-22 | User accepted Phase 1, independently tested cross-college RLS blocking, and authorized Phase 2 | Begin Talent Finder only; Phase 3 remains gated. |

| 2026-09-22 | Phase 2 uses configurable 40/20/20/15/5 matching weights with normalized 0-100 factors | Unvalidated starting assumptions over the five collected evidence types; no structured experience, trained model, embeddings, or confidence score. |
| 2026-09-22 | Apply CGPA/branch/backlog rules before primary-shortlist ranking; default score threshold 60 | Hard restrictions remain visible even for high-scoring profiles; scores never silently override eligibility. |
| 2026-09-22 | User approved a truthful fixed no-skill-gap exclusion variant | Preserve the exact requested template when a real gap exists; never invent a skill gap for branch/CGPA/backlog-only exclusions. |
| 2026-09-22 | Add company/job/match/audit tables with atomic FORCE RLS, college filters and composite tenant foreign keys | All nine tenant tables now have both enforcement layers; recruiters can access only their own company's drives. |
| 2026-09-22 | Store full calculation snapshots with recruiter promote/reject reasons; preserve overrides on rerun | Human judgment is auditable and does not alter the calculated score or hide eligibility restrictions. |
| 2026-09-22 | Expand seed.py to 300 students, 12 companies and three simulated drives | Preserve existing profiles; generate deterministic synthetic evidence and keep seed passwords unshared. |

| 2026-09-22 | User accepted Phase 2 including a manually verified explanation and override; authorized Phase 3 | Scheduling, analytics and rule-based support only. Phase 4 remains gated. |
| 2026-09-22 | Any future trained support-classifier upgrade must handle class imbalance with SMOTE or class weighting | Explicitly remind the user of this prerequisite if an upgrade request omits it. No classifier is built in Phase 3. |

| 2026-09-23 | Admin access is an explicit server-side allowlist of existing accounts | User selected one existing account in Demo College 1; its email stays out of public source/docs. No public admin signup; current role and allowlist checked on every request. |
| 2026-09-23 | Use half-open interview intervals, normalized resources, a seven-day greedy search and a college-scoped confirmation lock | Adjacent slots and independent drives are allowed; shared-resource overlaps are explained. Recheck at approval prevents stale and concurrent double-booking; old booking survives until reschedule approval. |
| 2026-09-23 | Support flag requires all three proposed thresholds; score is a count out of three | At least three role skill gaps, known interview score below 40, fewer than two completed interviews in the last 30 days. Missing scores remain unknown; activity is an opportunity/record proxy. No ML, probability or accuracy claim. |
| 2026-09-23 | Analytics reports shortlist conversion and advertised CTC; placement percentage remains null | Offers do not exist until Phase 4; a match, manual promotion or interview selection does not prove placement. |
| 2026-09-23 | Seed four support profiles and a genuine overlapping pair with stable keys | Three support examples meet all rules; a fourth has participation evidence. Restarts preserve reviews and resolved bookings. |

| 2026-09-23 | User explicitly confirmed Phase 3 live checks passed and accepted the phase | Fresh admin login opened Command Center; charts appeared, the scheduling conflict disappeared after approval, and the support review saved. No Phase 4 work starts without a new instruction. |

| 2026-09-23 | User reconfirmed Phase 3 and explicitly authorized Phase 4 | Implement separate offer stages, simulated in-app notifications, about 4,800 synthetic profiles and 40–50 companies, and frozen ten-profile evaluations. Stop before Phase 5. |

| 2026-09-23 | Phase 4 uses five distinct offer stages, versioned role-scoped actions, audit snapshots and recipient-only simulated notifications | Student acceptance remains student-owned; document exchange/verification occurs externally. New tenant tables retain application filters and FORCE RLS. |
| 2026-09-23 | Expand to 4,800 synthetic students/45 companies using noisy correlated preparation and fictional outcomes | Preserve earlier fixtures and human changes; label synthetic offers. Accepted offers and joining remain distinct analytics measures. |
| 2026-09-23 | Freeze assistant-authored evaluation expectations before execution in c2748bf | Reproduced 25/30 expected matches; readiness/support each agree on 10/10. Keep disagreements and sample limitations; no validated accuracy claim. |

| 2026-09-23 | Phase 4 lifecycle and final analytics demonstrated; separate delivery from user phase acceptance | Agent verified the synthetic student API workflow; user performed admin UI actions and supplied refreshed counts. Stop before Phase 5 until explicitly authorized. |

| 2026-09-23 | User accepted Phase 4 end to end and authorized Phase 5 | Final polish, security audit and demo documentation only; no stretch features. |
| 2026-09-23 | Verify actual PostgreSQL catalog policies at startup and health checks | Fail closed on policy drift; publish only safe configuration status, while retaining college filters and ownership/RBAC checks. |
| 2026-09-23 | Exact Vercel CORS with a local Vite /api proxy | Remove production wildcards without trusting arbitrary preview/local origins. |
| 2026-09-23 | Write implementation-grounded audit, judge sheet and click-by-click demo | Separate synthetic evidence, prior user browser acceptance and automated checks; do not reconstruct missing research or claim unsupported uniqueness. |

| 2026-09-24 | User authorized a hybrid public + synthetic data strategy and a metrics-first gate | Campus Recruitment public labels train a separate Random Forest placement-status signal; existing weighted readiness, matching and support remain separate. No frontend integration before reporting actual held-out results. |
| 2026-09-24 | Freeze source and training choices in cde4998 before the first run | Pinned Ben Roshan dataset mirror at ShuklaPrashant21/Campus_Recruitment, 215 rows; seed 42 stratified 80/20, 300 trees, leaf minimum 2 and balanced training class weights. No salary/ID/label leakage or test tuning. |

| 2026-09-24 | Measured public-data holdout results: 38/43 correct; accuracy 88.37%, Placed precision 93.10%, recall 90.00%, F1 91.53%; matrix [[11,2],[3,27]] | One frozen split/configuration on Campus Recruitment, not a synthetic sanity check. Small MBA cohort, 43 test cases, no external validation; source https://www.kaggle.com/datasets/benroshan/factors-affecting-campus-placement via pinned ShuklaPrashant21/Campus_Recruitment mirror. |

_Add a new row every time a meaningful architectural or product decision is made._

---

## 3. Current State

### ✅ Completed
- [x] 2026-09-24: BTech / BE extension deployed as bb3f743/API 0.8.0. Publisher-reported engineering dataset v6 (2,966 rows; 181 modeled profiles), fixed group-disjoint training/evaluation, four-field explained signal, no MBA requirement, nineteenth tenant table with application filters/ownership/FORCE RLS.
- [x] BTech verification: all 51 backend tests passed in one run; production frontend build and actual-output rendering passed. Live checks verified both models ready, all 19 policies, four additive factors, save/reload, unchanged MBA/readiness, missing/outside-source no score, access denials, restored original inputs and deployed frontend.
- [x] 2026-09-24: Integrated and deployed the public Campus Recruitment Placement Likelihood Model (e6eba59/API 0.7.0). Startup-only trusted loading; optional validated academic inputs with ownership/college filters and 18th FORCE RLS table; separate score, baseline, all 12 factors, explanation and measured evaluation panel. No weighted-rule, matching or support changes.
- [x] Public-model release checks: 46 backend cases passed across regression/retests; production frontend build, actual-output card rendering and dependency check passed. Live model ready, all 18 policies, owned save/reload, unchanged weighted readiness, missing evidence no score, unauthenticated/other-student/recruiter denials, and frontend bundle verified. Temporary public-row example on the authorized synthetic account was restored to its original academic inputs.
- [x] Five offline public-model validation checks passed: pinned source/structural salary, stratified disjoint split, excluded predictors/training-only encoding, saved-artifact metric reproduction and modified-source refusal. Dependency check passed; existing package versions, application code and synthetic evaluations are unchanged.
- [x] Imported the public Campus Recruitment CSV from a pinned GitHub revision with source/license/checksum: 215 rows, 148 Placed / 67 Not Placed. Kept it separate from all synthetic tenant records.
- [x] Trained the predeclared offline Random Forest on 172 rows and evaluated 43 stratified held-out rows. Actual metrics: accuracy 88.37%, Placed precision 93.10%, recall 90.00%, F1 91.53%; confusion matrix [[11, 2], [3, 27]] in Not Placed / Placed order. Saved the exact evaluated pipeline and full report under backend/ml/. No tuning or holdout refit.
- [x] Phase 5 release c3d7a57 deployed: exact DESIGN palette tokens, critical status styling, saffron numbered headings, explainability-first copy, preserved logos and static FAQ-only Jugaad Dost. No AI Mock Interview, live chatbot, trained classifier or embedding dependencies were built.
- [x] Locked CORS to https://jobjugaad.vercel.app with explicit methods/headers; live preflight accepts only that origin among tested real/foreign/lookalike/local origins. Local development uses the Vite /api proxy.
- [x] Verified all 17 live tenant tables with college_id, ENABLE/FORCE RLS and college_isolation USING/WITH CHECK predicates, plus a runtime role without superuser/BYPASSRLS. Application college filters and role/ownership controls remain. Per-table evidence: PHASE5_AUDIT.md and evaluations/phase5-security.json.
- [x] Audited readiness, matching, override-history and support screens: no bare-score failures found; all include factors and explanations. All 37 backend checks passed across the complete run and affected-suite retest; final frontend build and saved-data rendering passed.
- [x] Added the written Scalability & Deployment Approach in Architecture Section 9, exact named-fixture DEMO_GUIDE.md and implementation-grounded JUDGE_REVIEW.md. Historical overclaims and missing research references are not treated as validated evidence.
- [x] Phase 4 Definition of Done demonstrated on 2026-09-23: live profiling → matching → approved/selected interview → notifications → all five offer stages → refreshed outcome analytics, plus both written evaluation statements. User explicitly accepted Phase 4 end to end and authorized Phase 5 on 2026-09-23.
- [x] Delivered Phase 4 offers with five separate stages, audited role-scoped actions, version checks, student/admin views and simulated recipient-only notifications. All three new tables have application college filters and FORCE RLS (17 tenant tables total).
- [x] Verified the live test lifecycle through student 4805, drive 17, interview 7556 and offer 2385: profiling/matching, confirmed and selected interview, issued letter, student acceptance/document submission, admin verification and joined status. Agent API checks independently confirmed all six offer audit events, nine student notifications and idempotent notification reads; admin UI actions were performed by the user.
- [x] Finalized 4,800 seeded synthetic students and 45 seeded companies with noisy correlated preparation/outcomes; additional live test accounts are separate. Seed idempotence and increasing outcome proportions across CGPA groups passed locally.
- [x] Wrote frozen ten-profile matching and scoring evaluations: 25/30 expected matches reproduced, readiness bands 10/10 and support flags 10/10 agreement. Five matching misses and sample limitations are retained; these are assistant-authored synthetic checks, not validated accuracy.
- [x] Verified 34 local checks across the regression and targeted runs, production builds, actual-data React rendering, API 0.5.0/database health and live ownership/role denials. Deployed the interview save-feedback improvement in b35db06.
- [x] Phase 3 accepted by the user on 2026-09-23 after successful live admin login, visible dashboard charts, conflict resolution after approval and a saved support review. These authenticated browser results are user-verified, not agent-observed.
- [x] Delivered deterministic scheduling with five new tenant tables (schedules, interviews, calendar audit, support indicators and support reviews), application college filters, FORCE RLS, next-free-slot proposals, explicit approval, concurrent/stale approval protection and audit evidence.
- [x] Delivered admin KPI tiles, Recharts branch/skill shortlist conversion, advertised CTC statistics and honest unavailable placement percentage until Phase 4 offers exist.
- [x] Delivered rule-only support checks with all three named factors, score as a count out of three, plain-language explanations, recommended interventions and saved human reviews. No trained classifier or risk probability is claimed.
- [x] Seeded four synthetic support examples and a genuine double-booking pair; stable seed keys preserve the user's resolved conflict across redeployments.
- [x] Published Phase 3 implementation commits `3d27d16` and `9922077` to main. Vercel deployment `4frMbuFgqk47YnESCyqU2FFXvFBe` succeeded; public frontend serves the Command Center bundle. Render serves API 0.4.0 with all ten admin endpoints and PostgreSQL-connected health. Unauthenticated live admin analytics/calendar/support requests return 401. **Authenticated Phase 3 live flow checks were subsequently confirmed by the user.**
- [x] Passed 25 local PostgreSQL/rule/API tests, production frontend build, HTTP preview checks and React server-rendering checks against real local API responses. All new tenant tables were tested independently of application filters; concurrent/stale approvals and support-review preservation were covered.
- [x] User accepted Phase 2, manually verified a "Below Threshold" explanation and a working override, and authorized Phase 3.
- [x] Delivered Phase 2 Talent Finder to Vercel and Render from commit 97d5e58: recruiter signup/login, company profile, configurable drive creation, skill-gap statuses and explained weighted matching.
- [x] Added four Phase 2 tables with application college filters and atomic ENABLE/FORCE RLS, alongside recruiter ownership and tenant-consistent foreign keys.
- [x] Implemented fixed-template explanations, full normalized factor breakdowns, missing requirements and next steps; the user-approved no-skill-gap variant is tested.
- [x] Implemented audited manual promote/reject actions with evidence snapshots and preserved decisions after reruns.
- [x] Expanded the managed database to 300 seeded students and 12 seeded companies. Render logged 250 newly added students, 12 companies and three seeded matching runs.
- [x] Demonstrated three live recruiter drives against 301 profiles: Python Backend 8 shortlisted / 293 excluded; React Frontend 8 / 293; Java Graduate 26 / 275. These are synthetic outputs, not accuracy metrics.
- [x] Passed 14 local rule/PostgreSQL integration tests, all new Swagger endpoint checks, production frontend builds, dependency and whitespace checks. Verified live signup, drive creation, factor tables, three complete candidate lists, promote/reject audit persistence, HTTP 401 without auth and HTTP 404 across colleges.
- [x] User explicitly accepted Phase 1 on 2026-09-22 and independently confirmed that RLS blocks cross-college access.
- [x] User explicitly confirmed Phase 0 working and authorized Phase 1 on 2026-09-22.
- [x] Imported both user-supplied brand assets and verified PNG format and dimensions: horizontal 1600 × 533; poster 1254 × 1254. Phase 0 has been explicitly accepted.
- [x] Created the architecture's frontend portal/API/component/context folders and backend engine/router folders, with later-phase modules left unimplemented.
- [x] Created `backend/venv` using bundled Python 3.12.14, installed all nine requested packages, and saved the exact `pip freeze` output in `backend/requirements.txt`; `pip check` passed.
- [x] Implemented and locally verified `/health`, its Pydantic response contract, open Phase 0 CORS, `/docs`, and the OpenAPI schema. Executed `/health` through Swagger UI with HTTP 200.
- [x] Built the React/Vite/Tailwind landing page with both supplied logos; verified the production preview calls the backend and the retry button works. Local PostgreSQL is correctly shown as not configured.
- [x] Added `.gitignore`, safe environment examples, deployment configuration, and README instructions; verified that virtual environments, node_modules, and `.env` files are ignored.
- [x] Created initial commit `d39492c` on `feature/phase-0`, created `main` from the locally verified commit, and pushed `main` to the existing GitHub repository.
- [x] Deployed Render free Python web service `jobjugaad-api` from root `backend/`, using Python 3.12.10, `/health`, and the existing managed PostgreSQL instance. Public HTTPS health check returned HTTP 200 with `database: connected`.
- [x] Deployed Vercel Hobby project `jobjugaad` from root `frontend/`, with `VITE_API_URL=https://jobjugaad-api.onrender.com` for Production and Preview.
- [x] Verified the public Vercel page displays Backend connected, API Healthy, and PostgreSQL Connected; both supplied logo images load, and no browser errors or warnings were reported.

- [x] Implemented all five Phase 1 models with `college_id`, explicit application filters, student ownership checks, composite tenant foreign keys, and atomic ENABLE/FORCE PostgreSQL RLS policies.
- [x] Implemented student signup/login with bcrypt hashing and two-hour JWTs containing `user_id`, `role`, and `college_id`; privileged signup fields are rejected.
- [x] Implemented PDF resume extraction with pdfplumber, persisted profile text, size/page/text limits, and a parser timeout; verified local and live uploads.
- [x] Implemented the fixed 30/20/15/15/10/10 weighted readiness rule with all four official bands, six-factor evidence breakdown, plain-language explanation, methodology, and next step.
- [x] Built and verified branded signup/login, profile editing, resume text review, and readiness UI; Jugaad Dost is a static FAQ.
- [x] Seeded 50 synthetic profiles on the managed database; Render startup logs confirmed FORCE RLS initialization and creation of 50 profiles.
- [x] Passed six local PostgreSQL integration tests, Swagger endpoint checks, dependency checks, and production frontend builds. Verified live signup, login, saved profile/PDF text, explained readiness, HTTP 404 for cross-college access, and HTTP 401 for unauthenticated access.
- [x] Merged and pushed Student Core to `main` through `bb640a2`; Render deployment `dep-daovm3v40ujc73brlbc0` and the Vercel production deployment succeeded. Live Definition of Done demonstrated on 2026-09-22.

### 🚧 In Progress
- No implementation or deployment work remains for the authorized BTech extension. Interactive browser automation remains unavailable; HTTP/API, regression and component-render evidence is recorded separately.

### ⏭️ Next Up
- User can sign in as a student and open Profile → BTech Placement Likelihood Model → Add or edit BTech model inputs. No further feature is started. Preserve separate BTech, MBA and weighted-readiness outputs; support-classifier upgrades still require class imbalance handling.

---

## 4. Known Limitations / Honest Caveats

Keep this section current — it's exactly what a judge or mentor will ask about, and it's better to know your own gaps than be caught off guard.

- Matching and Weighted Readiness Score remain rule-based. The distinct public-data BTech and MBA Random Forests have their own input APIs and frontend cards; no merged score is claimed. Four BTech or twelve MBA contributions plus a training baseline explain uncalibrated scores, not personal placement probabilities. Original collections are publisher-reported; fairness, calibration and external validity are unverified. Inputs are not imputed. BTech requires no MBA data, but covers only six streams, semester-6 CGPA 5–9 and 0–3 internships.
- All 37 local rule/PostgreSQL checks passed across the complete Phase 5 run and targeted retest; the user confirmed earlier authenticated live lifecycle checks. Agent-driven Swagger UI and visual checks could not run because browser automation failed to initialize; HTTP/OpenAPI, integration and server-render checks are distinct evidence. Phase 4 written local checks reproduce 25/30 expected matches, with 10/10 readiness-band and 10/10 support-flag agreements. These are assistant-authored synthetic checks, not real-world accuracy or independent human validation.
- Notifications are implemented as simulated in-app records only; no email or SMS is sent. Offer/document stages record human declarations about external document exchange, not automatic document verification.
- The original seventeen Phase 1–4 tenant tables plus placement_model_profiles and btech_model_profiles (19 total) have college filters and FORCE RLS, with independent local cross-tenant tests. The API 0.8.0 live catalog verifies all 19 policies and the non-bypass runtime role; current evidence is in evaluations/btech-live-security.json. Demo college enrollment is self-selected, not verification of real institution membership; use synthetic details only.
- The application demo cohort remains synthetic: 4,800 seeded students and 45 companies plus synthetic walkthrough accounts. The separate classifier uses 215 imported public labeled records (172 train / 43 test), with measured internal holdout results. No external/BPUT validation, production-scale accuracy, latency benchmark or calibrated confidence is established.
- Readiness inputs are self-reported. Project count and mean skill proficiency are explicit, unvalidated normalization choices. PDF prose does not automatically create skills or change readiness.
- Browser JWTs are stored in sessionStorage and expire after two hours. Email verification, password reset, refresh tokens, server-side logout revocation, and rate limiting are not implemented.
- Local PostgreSQL test configuration is stored only under ignored .local/. The live Render service uses its existing managed PostgreSQL database.
- Render's existing free `Job-Jugaad` database expires on **2026-10-21**, as displayed in its dashboard. No paid upgrade was made.
- The existing database's external IP access rules were preserved; the application uses its internal Render connection. The stricter fresh-environment template in `render.yaml` has not been applied to this existing database.
- Phase 5 restricts CORS to https://jobjugaad.vercel.app; local development uses Vite's /api proxy. Live allowed/rejected-origin verification passed on 2026-09-23.
- Render's free tier cold-starts after 15 minutes idle — must warm up before live demos.
- Simulator (P2) is not implemented. Any future projections must be labeled as hypothetical outputs from the synthetic dataset's conversion model, not validated forecasts.
- Competing campus placement platforms exist; no first-mover or exclusive-feature claim is made. Demonstrate the implemented explanations, rule-based support and human-reviewed workflow. Historical research files are absent; the simulator is not implemented.
- AI Mock Interview is out of scope by decision, not by oversight. "Jugaad Dost" is a static label/FAQ panel, not a live chatbot, by decision.

---

## 5. Open Questions

_Track unresolved questions here so they don't get lost between sessions._

- [x] Use plain JavaScript for the frontend (Phase 0 decision).
- [ ] Do we attempt the pgvector semantic-matching stretch goal, or stop at keyword matching? (Default per `ARCHITECTURE.md`: stop at keyword matching for P0/P1, attempt only if time remains.)
- [x] Phase 4 seed.py implements 4,800 synthetic profiles and 45 companies, preserving earlier records and three matching demonstration drives.
- [x] User authorized a separate Campus Recruitment Random Forest signal on 2026-09-24, reviewed measured metrics, and requested integration/deployment. Weighted readiness remains unchanged.

---

## 6. Environment & Access Notes

_Do not put actual secret values here — only where to find them._

- `DATABASE_URL` — configured in Render dashboard (Web Service → Environment). Local test database credentials are stored only in ignored `.local/` tooling. The backend reads environment variables directly and does not automatically load `.env` files.
- `JWT_SECRET` — saved by the user in Render Environment settings; its presence in the saved configuration and successful JWT authentication were verified. No secret value is stored in documentation or git.
- `VITE_API_URL` — set in Vercel project settings (Environment Variables) and locally in `frontend/.env`
- Render web service: `srv-daol1s5g1s2s738prvhg`; managed PostgreSQL: `dpg-daokrdjm8hqs73f3cm60-a` (`Job-Jugaad`), Oregon.
- Vercel project dashboard: https://vercel.com/kamana5813/jobjugaad — root `frontend/`, Git branch `main`, Hobby plan.

---

## 7. Reference Documents

- `PRD.md` — what we're building and why
- `ARCHITECTURE.md` — how it's built (stack, schema, API, engines)
- `RULES.md` — how we write code and work together
- `PHASES.md` — the build order and current roadmap
- `DESIGN.md` — brand, UI, and voice guidelines
- `RESEARCH_AUDIT.md` — competitive research database; what's common vs. genuinely differentiated
- `TECHNICAL_VALIDATION.md` — research-backed validation of AI/ML, matching, readiness, scheduling design
- `REVISED_DOCUMENTATION.md` — full before/after refinement log that produced the changes now merged into these six files
- `JUDGE_REVIEW.md` — hard hackathon-judge questions, answered honestly — read this yourself before demo day

---

## 8. Session Handoff Notes

_When ending a work session, leave a short note here for whoever (or whatever AI agent) picks this up next._

> _(example format)_
> **Session ended:** [date]
> **What I just finished:** ...
> **What's broken/incomplete:** ...
> **What to do next:** ...

> **Session ended:** 2026-09-21
> **What I just finished:** Read all six project documents in the required order and saved both supplied logos at the requested asset paths.
> **What's broken/incomplete:** Application scaffolding and deployment have not started; no GitHub remote is configured. The horizontal logo has a black background in the supplied JPEG; conversion preserves it and does not add transparency.
> **What to do next:** Begin Phase 0 when requested. Use the supplied brand assets and follow DESIGN.md. Do not advance to Phase 1 until the user explicitly confirms Phase 0's Definition of Done.

> **Session update:** 2026-09-21 — Phase 0 implementation
> **What I just finished:** Installed requested dependencies; created and built the branded skeleton; verified API/CORS/OpenAPI, Swagger execution, frontend-to-backend communication, retry behavior, and git exclusions. Prepared Render and Vercel configuration.
> **What's broken/incomplete:** GitHub initial push and both deployments are pending. Render/Vercel account access needs the user's sign-in; no live URLs or PostgreSQL connectivity have been verified. No Phase 1 work has begun.
> **What to do next:** Commit and push to the existing Kamana5812/JobJugaad repository, deploy the Render Blueprint, configure Vercel root `frontend/` with access to root-level assets, and set `VITE_API_URL`. Confirm backend reports `database: connected` and the frontend receives that live result, then stop for the user's explicit confirmation.

> **Session ended:** 2026-09-21 — Phase 0 deployed
> **What I just finished:** Pushed the initial commit to GitHub, deployed the Render backend with the existing managed PostgreSQL instance, and deployed the Vercel frontend. Verified public HTTP 200 health with database connected and the live browser's successful frontend → backend → PostgreSQL check, logo loading, and absence of browser errors.
> **What's broken/incomplete:** No deployment blocker remains. Phase 0 still requires the user's explicit acceptance of both URLs. Local PostgreSQL is not configured. The free managed database expires on 2026-10-21. VS Code availability was not checked; development used Codex and the bundled Python runtime.
> **What to do next:** Ask the user to open https://jobjugaad.vercel.app and https://jobjugaad-api.onrender.com/health and confirm both work. Do not begin Phase 1 before that explicit confirmation. No Phase 1 functionality has been built.

> **Session handoff:** 2026-09-22
> **What I just finished:** Resumed Phase 0 handoff, rechecked both public URLs (HTTP 200; backend reports PostgreSQL connected), and finalized deployment notes in MEMORY.md, PHASES.md, and README.md.
> **What's incomplete:** The user's explicit confirmation of both live URLs is still pending. No Phase 1 functionality has been started.
> **What to do next:** Present both live URLs and wait for Phase 0 acceptance.

> **Session update:** 2026-09-22 — Phase 1 implementation
> **Finished locally:** Five tenant models and atomic FORCE RLS; student auth; profile and PDF endpoints; weighted readiness with breakdown/explanation; 50-profile idempotent seed; student frontend. Six PostgreSQL integration tests passed and the production frontend build passed. Swagger exercised all new endpoint types before frontend integration.
> **Still pending:** Finish browser UI checks, configure live JWT_SECRET, commit/push the verified code, deploy and verify the Phase 1 flow on Vercel/Render.
> **Next gate:** Stop when the Phase 1 live Definition of Done is demonstrated; do not start Phase 2 without explicit user acceptance.
> **Browser verification:** Local signup/login, profile save and recalculation, persistence after a fresh login, and PDF upload/text review succeeded. The synthetic profile returned 62/100 (Developing) with six contributions and explanation. No application console errors or warnings were reported. Live deployment is still pending.

> **Release handoff:** 2026-09-22
> **Ready:** Student Core implementation committed as `0cc7e1d` and pushed to `feature/student-core`. Backend integration tests, Swagger endpoint checks, frontend build, signup/login, persisted profile/readiness, and PDF text review passed locally. Final dependency check and git whitespace check passed.
> **Deployment dependency:** The existing live Render service needs `JWT_SECRET`. Its Environment editor has a prepared `JWT_SECRET` row with a Generate button; the user was asked to generate and save it because browser credential entry/submission requires user handoff. Do not put the generated secret in chat or git. Current live main still serves Phase 0.
> **Next:** Once the secret is saved, merge the verified feature branch into main, push, verify Render initializes FORCE RLS and 50 synthetic students, and exercise the live Vercel Student Core flow. Then update phase completion records and stop for the user's Phase 1 acceptance. No Phase 2 work is authorized.

> **Session handoff:** 2026-09-22 — Phase 1 delivered
> **Finished:** Verified the user's saved JWT_SECRET configuration, fast-forwarded Student Core into main, and confirmed successful Render and Vercel deployments. Render logged FORCE RLS initialization and 50 new synthetic profiles. A synthetic student signed up through the live Vercel UI, uploaded a PDF, reviewed extracted text, and saved profile evidence. The live UI and API returned 62/100 (Developing), with contributions 21/5/12/9/7/8, all factor evidence, and an explanation. Live login/persistence and cross-college/unauthenticated denial checks passed.
> **Limitations:** Synthetic demonstration and self-reported inputs only; no placement accuracy claim. Managed free database expires 2026-10-21. CORS restriction remains scheduled for Phase 5. The optional final browser reload check was initially interrupted by an approval-review usage limit, then resumed after the user asked to continue.
> **Next:** Present https://jobjugaad.vercel.app and https://jobjugaad-api.onrender.com/docs for review. Wait for explicit Phase 1 acceptance; do not start Phase 2.


> **Phase gate update:** 2026-09-22 — User confirmed Phase 1 working, explicitly confirmed their own RLS cross-college blocking test, and authorized Phase 2 Talent Finder. Re-read Architecture Section 5 in full before Phase 2 implementation. Stop after Phase 2''s live Definition of Done; Phase 3 requires explicit acceptance.

> **Session update:** 2026-09-22 — Phase 2 implemented locally
> **Finished:** Recruiter/company auth, drive creation, four new tenant tables with atomic FORCE RLS, skill-gap comparison, configurable normalized weighted matching, score/factor/explanation responses, pagination and audited promote/reject actions; 300 synthetic students, 12 companies and three seeded simulated drives. Recruiter UI production build passed. Fourteen local rule/PostgreSQL tests passed, including all nine tenant tables, company ownership, threshold boundaries, exact keywords and preserved overrides. New endpoints were exercised through local Swagger before frontend integration.
> **Decision:** User approved the fixed truthful no-skill-gap exclusion variant. Matching weights 40/20/20/15/5 are explicitly unvalidated; see Architecture Section 5 for normalization and eligibility details.
> **Pending:** Finish UI review, commit and deploy Phase 2, demonstrate three live drives, then update completion records and stop for Phase 2 acceptance. Phase 3 remains gated.

> **Session handoff:** 2026-09-22 — Phase 2 delivered
> **Finished:** Published commit 97d5e58 to main. Render deployment dep-dap8avp7lnhs73avdrlg and Vercel production deployment HTw4jiBy6ComWSXZLVCcJaQhYAZC succeeded. Live recruiter signup and drive creation worked through Vercel; complete explained candidate results were verified for Python, React and Java drives. Render confirmed FORCE RLS startup plus 250 additional students and 12 companies. Live API checked all factor sums, descending order, fixed explanations, manual promotion/rejection evidence, preserved overrides on rerun and cross-college/unauthenticated denial. Local UI showed the preserved eligibility restriction beside the human exception and saved audit reason.
> **Honesty:** There are 300 seeded profiles plus one earlier synthetic live-check student in the tested college. Three-drive counts were captured before manual smoke-test overrides. This is a deterministic synthetic demonstration, not calibrated confidence or validated placement accuracy. Phase 4's self-labeled sanity evaluation remains pending.
> **Next:** Present https://jobjugaad.vercel.app/recruiter/signup and https://jobjugaad-api.onrender.com/docs. Wait for explicit Phase 2 acceptance; do not begin Phase 3.

> **Phase gate update:** 2026-09-22 — Phase 2 accepted by the user, including manual explanation and override verification. Begin Phase 3 only. Read all six root documents in order. Admin account selection is pending while implementation proceeds. Stop after the live Phase 3 Definition of Done.


> **Session update:** 2026-09-23 — Phase 3 implemented locally
> **Implemented:** Five tenant tables with atomic FORCE RLS and college filters; allowlisted admin auth; deterministic greedy scheduling with pending approval, concurrency/version protection and audit history; analytics from actual records; rule-only support indicators with factors, interventions and human review; idempotent conflict/support fixtures. Frontend adds the branded Command Center, Recharts conversion views, scheduling forms and explained support review.
> **Verification:** All 25 backend rule/PostgreSQL tests passed, including all ten admin endpoint contracts, status timing, simultaneous approval, stale versions, composite foreign keys and independent RLS on all new tables. Production frontend build passed with admin charts loaded separately. Server rendering against actual local API responses passed for analytics, the seeded conflict/proposals and 94 explained support cards in the accumulated local test dataset. One intervening run hit a transient database connection timeout; the complete sequential rerun passed. Browser automation fails during initialization, so Swagger UI execution and interactive visual verification remain pending.
> **Admin setup:** User selected an existing Demo College 1 account. The exact email/configuration is in the private task conversation, not this public file. Render configuration and live provisioning are pending confirmation.
> **Next gate:** Complete live Phase 3 verification before marking it delivered. Do not start Phase 4.


> **Deployment handoff:** 2026-09-23 — Phase 3 release published
> **Finished:** Fast-forwarded `feature/admin-scheduling` to main and pushed `9922077`. Vercel reported successful deployment `4frMbuFgqk47YnESCyqU2FFXvFBe`. Live frontend `/admin` returns 200 and loads `AdminPage-B2ZxoLxy.js` with the new interface. Render OpenAPI reports 0.4.0 and all ten admin operations; health returns 200 with PostgreSQL connected. Public admin analytics/calendar/support requests correctly return 401. Initial Render health timed out during startup; the retry succeeded.
> **Still pending:** User must save the requested Render `ADMIN_ACCOUNTS` setting for the exact existing account selected in chat, then log out/in using Demo College 1. Browser automation failed repeatedly before initialization with “failed to write kernel assets: The system cannot find the path specified”; one reset did not resolve it. No authentication secret was read or changed. Swagger HTML and OpenAPI/API contracts were tested over HTTP, but Swagger UI execution and interactive visual/live admin verification could not be performed. Do not describe those checks as passed.
> **Next:** Resume browser access (may require restarting the Codex app), confirm the Render setting, then use the user's authenticated admin session to inspect charts, resolve the seeded double-booking through proposal and approval, and review support factors/interventions. Local preview is at http://127.0.0.1:5176 with API/docs at http://127.0.0.1:8003/docs; its synthetic admin is local-only. Update Phase 3 completion only after live flow verification. Phase 4 remains unstarted.


> **Admin provisioning follow-up:** 2026-09-23
> **Evidence:** User supplied logs for Render deployment `dep-dapjme67bikc73fo2tsg`: dependency installation/build succeeded, but startup failed in `provision_admin_accounts()` because a configured email/college pair does not exist. This is not a package-installation or database-connection failure. The allowlist is configuration, not account creation.
> **Current availability:** Rechecked live health (HTTP 200, PostgreSQL connected) and the Vercel signup page (HTTP 200). The existing deployment remains available for registration.
> **Next:** User creates the selected account through normal signup in Demo College 1, using a private password, then chooses Render Manual Deploy / Deploy latest commit. After success, log out/in to receive an admin token and finish authenticated Phase 3 verification. Do not silently create an admin password or relax the allowlist. Browser automation still cannot initialize. This note is committed locally on the feature branch; defer publishing it until registration to avoid triggering another known-failing deployment.


> **Registration follow-up:** 2026-09-23
> **User report:** The selected account has been registered and Render redeployed. Rechecked live health: HTTP 200, PostgreSQL connected; OpenAPI 0.4.0 exposes all ten admin operations and the live admin page returns 200.
> **Pending:** Fresh login with Demo College 1 must show Placement Command Center. User was asked which screen appears. Browser automation still fails before initialization, so authenticated admin access, live chart rendering, seeded conflict resolution/approval and support review are not yet independently verified. Do not infer successful promotion merely from public health. The user's previously open localhost:8001 Swagger tab is an older local API, not the live deployment.


> **Phase 3 acceptance handoff:** 2026-09-23
> **Finished:** User confirmed a fresh login opens Placement Command Center, then answered yes when explicitly asked whether charts appeared, the scheduling conflict disappeared after approval and the support review saved. Phase 3 Definition of Done is accepted. Updated Completed, cleared In Progress and moved Next Up to the Phase 4 instruction gate.
> **Evidence boundaries:** Twenty-five local backend tests, frontend production build and actual-data React rendering passed. Agent checked live health/database connectivity, API version/routes, deployed bundle and unauthenticated denial. The authenticated dashboard/scheduling/support checks were performed and confirmed by the user. Browser automation and Swagger UI execution were unavailable; no claim that the agent independently performed those checks.
> **Next:** Wait for an explicit Phase 4 request. Do not start offers, notifications, large-data expansion, evaluations or later phases yet. Future support-classifier upgrades still require SMOTE/class weighting; current implementation remains simple rules only.


> **Phase 4 start:** 2026-09-23 — User reconfirmed Phase 3 and authorized Phase 4. Reread PRD, Architecture (including Section 9), Rules, Phases, Design and Memory in order. Freeze manually inspected expected results before running the evaluation engines; identify assistant-authored synthetic judgments honestly and report observed counts/mismatches without real-world accuracy claims.


> **Phase 4 local progress:** 2026-09-23 — Implemented offers, audit events and simulated recipient feeds with RLS; added student/admin views, correlated seed expansion and written evaluation reports. Six offer tests and production build passed. Actual-data React rendering checks all five stages/history and outcome analytics; this does not replace browser interactions. Full regression rerun includes batched support persistence and dataset integrity checks. Browser automation still fails initialization (missing kernel-assets path), so Swagger UI and live authenticated UI checks remain unverified. Next: complete regression checks, deploy tested code, verify live lifecycle, then stop for Phase 4 acceptance. Do not start Phase 5.

> **Phase 4 release preparation:** Implementation committed as `753da3c`. The 33-check regression run passed 32 checks and caught SQL null handling in excluded candidate filtering; after correction all eight matching checks passed, including that regression and override preservation. Final frontend production build passed. Browser initialization still fails after reset. Generated live synthetic-test credentials will remain under ignored `.local/`; never commit or print them. Deploy next, then verify live records and obtain the user's authenticated admin/student walkthrough before claiming the Phase 4 Definition of Done.

> **Phase 4 deployment handoff:** 2026-09-23 — Release `e52147c` is pushed to main. Vercel reports success and its public bundle contains My offers and the simulated feed. Render now serves OpenAPI version 0.5.0 with offer/notification routes; health reports PostgreSQL connected. Unauthenticated requests to admin offers, eligible interviews, notifications and student offers each returned 401. This is public HTTP evidence, not authenticated browser verification.
> **Remaining gate:** Automatic approval review rejected creating one persistent live synthetic student, recruiter/company and drive because it requires explicit approval for those production additions. The prepared ignored `.local/phase4-live-smoke.py` did NOT execute and no test accounts were created by it. The user has a pending explicit approval question. Do not bypass the rejection. Browser automation also still fails initialization with a missing kernel-assets path, so the user's admin actions are needed for the live walkthrough. Generated test credentials must remain in ignored `.local/`, never in chat or git. Phase 4 is deployed but its live Definition of Done is not yet satisfied; Phase 5 remains gated.

> **Phase 4 live walkthrough resumed:** User replied continue to the explicit synthetic-record request; automatic approval review then allowed the described operation. Created one labeled synthetic student (4805), recruiter/company and drive (17), with generated credentials only in ignored `.local/phase4-live-test.json`. Live profile save/readiness and matching passed; the target student's match includes factors and explanation. Student-owned offers/feed return 200; student and recruiter access to admin offers returns 403. User reported scheduling approval, but the student's feed was still empty on independent read, so asked whether the proposal is actually in the confirmed calendar for student 4805. Do not infer a completed booking or offer workflow until verified. Browser initialization remains unavailable.

> **User deferred verification:** The user reported the booking appears as scheduled, but the synthetic student's feed returned no notifications on two independent reads. Asked for the card details to disambiguate; user replied “i will verify it after now proceed.” Respect that deferral: do not keep asking for the same check, infer completion, access their credentials or provision another administrator. Frontend configuration was independently confirmed to point to the same live Render API. Remaining live actions: verify student 4805/drive 17 booking; after its end record Selected; create and issue its offer; use the saved synthetic student account to accept and declare document submission; administrator verifies and records joining; confirm feed/history and analytics. All these admin actions remain unverified. Phase 5 is not authorized.

> **Final local check for this handoff:** The focused PostgreSQL interview-notification test passed: approved booking creates one recipient-owned notification with the correct drive/venue; another student and another college receive 404 when attempting to mark it read; the owner can mark it read. There are now 34 checks verified across the regression and targeted runs. No live admin or offer completion is inferred from this local result. Phase 4 implementation is deployed and ready for the deferred live walkthrough; Phase 5 remains gated.

> **Phase 4 status-save diagnosis:** User reported that Save interview status did not work. The supplied card was the different seeded “Simulated Python Backend Engineer” interview in demo hall/panel, ending 2026-09-24 10:30 AM, not target drive 17/student 4805. Its future end explains the server's outcome-time restriction. Found a separate feedback usability issue: interview errors appeared only in the Pending approval section, away from the clicked button. Added inline result messages beside each status button, an explicit end-time instruction, a reason-length hint and a saving label. Refresh failure after a successful mutation is now distinguished from an unsaved change. Production build passed; backend permissions/time checks are unchanged. Guide the user to choose exact test drive 17/student 4805 before continuing; no live offer completion or Phase 4 acceptance is claimed.

> **Phase 4 final live workflow evidence:** Offer 2385 for synthetic student 4805 / drive 17 / selected interview 7556 is issued, documents submitted, verification verified, acceptance accepted and joining joined. The user performed admin issuance/verification/joining; agent performed the authorized synthetic student responses. Agent independently read the final stages, all six audit actions and nine recipient notifications, and confirmed marking the joining notification read is idempotent. The earlier card for another student was a different booking; do not infer changes to that student's records. Remaining final check is the refreshed admin outcome counts; user has been asked to copy them. Browser automation remains unavailable, so authenticated admin screen observations are user-provided.

> **Phase 4 delivered:** 2026-09-23 — User supplied refreshed Overview values: 1,418 distinct students with active accepted offers, 701 recorded joined, 2,385 offers total, with 2,383 marked as seeded synthetic offers. Active accepted CTC: min 3.00, mean 3.34, max 6.50 LPA. These are live demonstration-record counts, not hiring accuracy or validated outcomes. They include the completed synthetic test offer 2385; the earlier other-student draft 2384 was left unchanged. The synthetic import flag marks seeded offers; manually created test records also remain fictional, as their names/reasons disclose.
> **Evidence and completion:** Agent API verified profile/matching evidence, approved/selected interview notifications, all five final stages, six audit events, nine recipient notifications and idempotent read state. User performed and confirmed admin UI actions and supplied dashboard counts. Thirty-four local checks, production builds and actual-data React rendering passed. Both written evaluations remain frozen at 25/30 matching hits and 10/10 readiness/support agreements, explicitly synthetic and assistant-authored. Phase 4 Definition of Done is satisfied for handoff; no independent agent browser/Swagger or student-browser-interaction claim is made.
> **Next:** Present the live app and evaluation report, then wait for explicit Phase 4 acceptance and Phase 5 authorization. No Phase 5 work has begun. Credentials and detailed authenticated test responses remain only in ignored `.local/`.

> **Phase 5 authorized:** User explicitly confirmed Phase 4 working end to end and requested the final polish/security/documentation pass. Read the six project documents; JUDGE_REVIEW.md and several historical research-reference files are absent from this checkout. Prepare a new implementation-grounded judge sheet and do not claim those missing sources were read. No trained model, live chatbot, mock interview or semantic-matching upgrade is authorized.

> **Phase 5 local verification:** 2026-09-23 — Exact Vercel CORS, live catalog isolation reporting, DESIGN palette cleanup, critical-status styling and numbered headings are implemented. The complete regression run passed 36/37; the notification assertion counted two different interviews from shared test setup. Scoped it to the baseline interview ID and all 12 affected tests passed on retest, covering 37 checks across runs. Final Vite build, offer/analytics rendering, readiness/10 matching/94 support-card rendering passed. No failed bare-score screen was found. Wrote PHASE5_AUDIT.md, DEMO_GUIDE.md, JUDGE_REVIEW.md and Architecture Section 9 scalability statement; cleaned unsupported active claims. Browser initialization still fails before opening a session, so no visual/Swagger rehearsal is claimed. Next: deploy and read the actual live 17-table policy report plus exact-origin CORS responses; then record final evidence. No stretch features.

> **Phase 5 final handoff:** 2026-09-23 — User Phase 4 acceptance is recorded. Release c3d7a57 is live on https://jobjugaad.vercel.app and https://jobjugaad-api.onrender.com (API 0.6.0). Public HTTP checks verified connected health, all 17 actual ENABLE/FORCE college_isolation policies and non-bypass runtime role, exact-origin CORS, protected-route 401 responses, and the deployed frontend bundle/API target. Saved safe public evidence in evaluations/phase5-security.json and listed each table in PHASE5_AUDIT.md. No private credentials or authenticated profile payloads were published.
> **Validation:** 36/37 passed in the full run; the notification assertion counted another test's separate booking. Scoped it to its own interview ID, then all 12 affected scheduling/support tests passed: 37 checks covered across runs. Final build and real saved-data rendering (readiness, 10 candidate cards, 94 support cards, student/admin offers and analytics) passed. No failing score screen. No AI Mock Interview/live chatbot/embedding upgrade; supplied tagline and requested Run AI Matching label remain with an explicit rule-based disclosure.
> **Delivered:** DEMO_GUIDE.md names student 4805 / drive 17 / interview 7556 / joined offer 2385, visible seeded matching candidates 2003 and 4499, the original support-student double-booking fixture, and a fresh-run conflict/lifecycle alternative. JUDGE_REVIEW.md and Architecture Section 9 provide honest evaluation and multi-college deployment explanations. The user accepted Phase 4 browser behavior; browser automation remains unavailable, so a Phase 5 visual/click rehearsal, reading aloud and actual pre-demo warm-up remain presenter actions. Stop here for user review; no stretch work is authorized.

> **Hybrid data start:** 2026-09-24 — User explicitly requested Campus Recruitment public CSV, an offline Random Forest training/evaluation pipeline, and a stop to show real held-out metrics before frontend integration. Retrieved the requested CSV from a pinned GitHub mirror; verified 215 rows, 15 columns, 148 Placed / 67 Not Placed and recorded SHA-256. Kaggle lists CC0 and describes anonymized campus data provided for classroom work; original collection is not independently audited. Frozen protocol/source/code committed as cde4998 before training. The sample is MBA-oriented and cannot be assumed representative of BPUT engineering cohorts. No frontend, tenant schema, seed records, rules or live deployment changed. Next: finish dependencies, train once, reproduce saved-artifact metrics, update actual results, then stop for review.

> **Public-model metric-review handoff:** 2026-09-24 — Trained once using the cde4998 frozen source/protocol. Measured held-out results: 38/43 correct, accuracy 88.37%, Placed precision 93.10%, recall 90.00%, F1 91.53%. Matrix rows actual / columns predicted, order [Not Placed, Placed]: [[11,2],[3,27]]. Dataset n=215; train=172 (118 Placed/54 Not Placed), test=43 (30/13). Majority baseline 69.77%. No test-set tuning, synthetic labels, salary/ID predictors or refit on the holdout.
> **Saved:** backend/data/Placement_Data_Full_Class.csv and source/license/checksum notes; backend/ml/train_readiness_model.py, training_protocol.json, readiness_model.joblib, evaluation_report.json and readable EVALUATION.md. pandas/scikit-learn/joblib and transitive versions are pinned. Five offline tests and pip dependency check passed. Saved model predictions independently reproduced the reported metrics.
> **Boundary:** Public labeled data is publisher-described campus recruitment data, not independently audited. Small MBA-oriented cohort and 43-case internal holdout do not establish BPUT, external or production-grade performance; probabilities are uncalibrated, and gender/education predictors need bias review before operational use. Weighted readiness, rule-based support, matching/skills/projects/certifications, tenant data and all prior synthetic evaluation artifacts remain unchanged. No frontend/API/schema/startup integration or production deployment was performed. Work stays on feature/public-placement-model for metric review. Next: show actual numbers and stop; subsequent integration must collect compatible fields, load once at startup and return separate explained outputs.

> **Integration authorization:** 2026-09-24 — User requested integration for deployment after the measured metrics were shown, and clarified that a real public dataset need not be from BPUT. Proceed with the existing Campus Recruitment artifact and optional compatible academic fields. Keep weighted readiness separate, expose local model-factor explanations, retain synthetic workflow records and all RLS/ownership rules. No newly collected BPUT dataset is required.

> **Public-model integration local handoff:** Optional academic profile persistence, GET/PUT placement-model endpoints, trusted startup loading, health status and separate frontend card are implemented. Exact tree-path contributions reconstruct forest predictions for all 215 source rows; missing inputs and failed checksum checks produce no score. Four new integration tests passed, production Vite build and available/missing/dirty card rendering passed, and pip check found no conflicts. Browser automation still fails before session initialization, so no click or Swagger UI verification is claimed. The long-interrupted full regression passed 45/46; its final matching case is being rerun in a fresh authenticated session. Automatic review initially could not run Git fetch because of its usage limit; the normal approval path was retried after the user said continue. No bypass was attempted.

> **Integration ready for deployment:** All 46 cases passed across full/targeted runs: 45/46 in the six-hour-interrupted regression, all eight matching cases in a fresh run, and all four model cases after the explicit update-filter improvement. Frontend build, actual-output card rendering, pip check and whitespace checks passed. Git fetch through the normal approval path succeeded after the review-service interruption; origin/main has no divergent changes. Next: fast-forward main, push and verify API 0.7.0/model ready/all 18 policies plus the deployed form, then record actual live evidence.

> **Public-model deployment complete:** 2026-09-24 — Release e6eba59 is live on https://jobjugaad.vercel.app and https://jobjugaad-api.onrender.com (API 0.7.0). Model artifact loaded successfully on Render using pinned dependencies; /health reports placement_model=ready and verifies every one of 18 tenant policies. Vercel reports success and its production bundle includes both separately named scores and the academic-input form. Live smoke test used public source row 1 temporarily on the existing authorized synthetic account, checked all 12 factors and additive reconciliation, saved/reloaded inputs, unchanged readiness and missing-input handling, and restored original inputs. No real account-holder academic history was inferred, no source rows were turned into fictitious tenants, and no credentials/private profile data were published. Safe evidence: evaluations/placement-live-security.json. Browser automation still cannot initialize, so a click-through rehearsal is not claimed. User-facing next step: Student profile → Placement Likelihood Model → Add or edit academic model inputs. No further scope started.

> **BTech extension start:** 2026-09-24 — User explicitly requested BTech integration. Retrieved Engineering Placements Prediction version 6 from Tejashvi/Kaggle (publisher CC0; 2013–2014 university records, original collection not independently verified). Source has 2,966 rows, 1,639 placed/1,327 not, but only 181 distinct four-field profiles. Freeze one group-disjoint first-fold split before training; keep identical modeled inputs together. Use semester-6 CGPA, engineering stream, internship count and ever-backlog history; exclude age/gender/hostel as a design choice, not a fairness claim. No MBA inputs or readiness-rule changes.

> **BTech measured results:** Fixed protocol committed in e5d4169 before training. One run, 2,374 training / 592 test rows, 140/41 distinct input groups with no overlap. Accuracy 83.95% (497/592), Placed precision 96.77%, recall 73.39%, F1 83.48%, matrix [[257,8],[87,240]], majority baseline 55.24%. Reported results to the user before frontend integration. Implemented optional four-field owned profile, nineteenth FORCE RLS table, startup loading, shared exact factor attribution, separate BTech and MBA UI panels. No model decisions enter recruiting rules. Missing/outside-source inputs yield no score. Five BTech tests and four MBA integration tests passed; full regression and release checks next.

> **BTech release ready:** All 51 backend tests passed in one complete run (364 seconds). Five new engineering tests verify group-disjoint evaluation reproduction, all 181 distinct-profile explanations, missing/outside-source/artifact failures, owned persistence and independent RLS. Existing MBA explanations still reproduce all 215 source rows. Production Vite build and actual-output BTech card rendering passed. Browser automation still fails kernel initialization; no click or Swagger UI rehearsal is claimed. No new dependencies. Next: publish the tested branch and verify both loaded models, all 19 policies, owned BTech persistence and the deployed form.

> **BTech final handoff:** 2026-09-24 — Application release bb3f743 is live at https://jobjugaad.vercel.app and https://jobjugaad-api.onrender.com, API 0.8.0. Both trusted models report ready. The live catalog verifies all 19 FORCE RLS policies. Authorized synthetic-account smoke test used a public engineering row temporarily and passed owned save/reload, score plus four factors/explanation, additive reconciliation, missing/outside-source input handling, unchanged MBA and weighted readiness, unauthenticated/other-student/recruiter denial, original-input restoration and frontend bundle verification. Safe evidence: evaluations/btech-live-security.json. All 51 backend tests, frontend build and component rendering passed; browser initialization still fails, so no interactive click/Swagger test is claimed. BTech evaluation remains 83.95% accuracy, 96.77% precision, 73.39% recall, 83.48% F1 on 592 held-out rows / 41 groups; older publisher-reported data and repeated profiles preclude current-campus or calibrated probability claims. Student path: Profile → BTech Placement Likelihood Model → Add or edit BTech model inputs. No further scope started.


> **Navigation preview handoff:** 2026-09-24 — User supplied new SVG logos, favicon, mascot and a navigation brief, with an explicit stop after landing and role selection for visual review. Implemented the scrolling landing, before/after section, three portal links, full saved synthetic matching example, unified `/auth` role cards, role-specific existing signup/login requests, `/student` canonical route, legacy redirects and verified-role guards. Fixed the old login success redirect (`result.roleHome(...)` was invalid); destination now uses `result.user.role`. Admin remains sign-in only. JWT verification, API permissions, RLS, model scores and existing dashboards remain intact.
> **Preview:** http://127.0.0.1:5174/ and http://127.0.0.1:5174/auth; Vite development-only proxy targets the existing Render API, with production CORS unchanged. Supplied light/dark logos and favicon are used. Built-in imagegen produced `frontend/src/assets/hero/landing-journey.png`; prompt/source recorded beside it. The three dashboard heroes and all dashboard redesigns are deliberately deferred to the user's review gate.
> **Checks:** Production build and 18 component/request-routing checks passed; saved example factors reconstruct its actual synthetic score. Browser automation still fails kernel initialization, so visual/click verification is not claimed. Local landing/auth HTTP checks passed and the development proxy correctly denied anonymous `/auth/me` with 401. This is a local preview, not a new production release. Next: user reviews landing and role selection; only then continue dashboard visuals and the other three heroes.
