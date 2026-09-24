# JobJugaad

An **explainability-first** campus placement platform for BPUT Hackathon 2026's CampusLink problem statement.

Phases 0–4 are deployed and explicitly accepted. Phase 5 is deployed with final UI, restricted CORS, live isolation auditing and presentation documentation; evidence and remaining presenter actions are in [PHASE5_AUDIT.md](PHASE5_AUDIT.md).

- Frontend: [jobjugaad.vercel.app](https://jobjugaad.vercel.app)
- Backend: [health](https://jobjugaad-api.onrender.com/health) · [interactive API](https://jobjugaad-api.onrender.com/docs)
- Repository: [Kamana5812/JobJugaad](https://github.com/Kamana5812/JobJugaad)

## Student flow

Create a student account using synthetic details and Demo College 1 or 2. Use the same college when logging in. Upload a text-based resume PDF, review the extracted text, then record skills, projects, CGPA, and existing assessment results. Save to recalculate readiness. Every response and score display includes six factors and an explanation.

Enrollment is self-selected for this hackathon demo, not verification of real college membership. Student JWTs cannot authorize recruiter actions or access another student's profile, even within the same college. Recruiters register a separate demo account and company; administrator signup is unavailable. Do not use real student data until institution-controlled enrollment and operational hardening are implemented.

## Readiness methodology

This is a **proposed weighted rule**, not a trained model or a validated placement prediction.

| Factor | Normalization to 0–100 | Weight |
|---|---|---|
| Technical skills | Mean of recorded self-reported proficiencies | 30% |
| Projects | 25 points per recorded project, capped at 100; quality is not assessed | 20% |
| Academics | CGPA × 10 | 15% |
| Aptitude | Existing self-reported assessment / 100 | 15% |
| Communication | Existing self-reported assessment / 100 | 10% |
| Interview | Existing self-reported assessment / 100; no interview feature | 10% |

Unrecorded factors contribute zero and are explicitly marked missing. Factor values and weighted contributions are rounded half-up to two decimals. Contributions are summed and the total rounded half-up to an integer before applying the official bands: 0–40 Not Ready, 41–65 Developing, 66–85 Ready, 86–100 Highly Employable. Certifications, backlogs, and resume prose are retained but do not add points to this formula.

No real-outcome validation has been performed for this weighted readiness rule. The separate public-data classifier has its own measured held-out evaluation below. The assistant-authored synthetic face-validity review is documented in [evaluations/phase4-report.md](evaluations/phase4-report.md); it is not independent validation.

## Recruiter flow and matching

Open [Talent Finder signup](https://jobjugaad.vercel.app/recruiter/signup), use synthetic company details and Demo College 1, then create a drive. Enter CTC in INR lakh/year, minimum CGPA, maximum backlogs, eligible branches and skill targets. The **Run AI Matching** button uses a keyword/weighted rule, not a trained model. The label follows the requested design; the adjacent copy states the actual method.

Starting weights are **unvalidated assumptions**: skills 40%, project keyword coverage 20%, academics 20%, existing assessments 15%, and certificate count 5%. Each component is normalized to 0-100 before weighting. The form allows per-drive weights summing to 100%, a minimum score (default 60), and an assessment review benchmark. See Architecture Section 5 for exact formulas and rounding.

CGPA, branch and backlog rules determine initial eligibility. Only candidates passing those rules and the score threshold enter the primary shortlist. Excluded candidates keep diagnostic scores, full factors, specific missing requirements, fixed explanations and a next step. Skill statuses compare self-reported proficiency with role targets: on-track at target, critical below half target, gap otherwise. No numeric confidence is reported.

Recruiters can promote or reject any candidate with a reason. The audit records reviewer, time, previous decision and full score/evidence snapshot; reruns preserve these manual decisions. Audit rows have no edit/delete API. This is review support, not an autonomous hiring decision.

### Live synthetic demonstration — 2026-09-22

| Simulated drive | Profiles reviewed | Shortlisted | Excluded |
|---|---:|---:|---:|
| Python Backend Engineer | 301 | 8 | 293 |
| React Frontend Engineer | 301 | 8 | 293 |
| Java Graduate Engineer | 301 | 26 | 275 |

These are actual live outputs before manual smoke-test overrides: 300 seeded students plus one earlier synthetic check profile. They are **not accuracy or benchmark claims**. The later Phase 4 self-labeled sanity evaluation is documented in [evaluations/phase4-report.md](evaluations/phase4-report.md). Seed-company passwords are unshared; create drives under your own recruiter account to run the same workflow.

Live checks verified all three candidate lists, five factor sums per result, descending order, explanations, promote/reject audit snapshots, persistence after rerun, HTTP 401 without authentication and HTTP 404 across colleges. All new endpoints were also exercised via local Swagger before frontend integration.

## Run locally (PowerShell)

Use Python 3.12, Node.js 24, and PostgreSQL. Create a database whose application role owns it but has neither superuser nor BYPASSRLS privileges. Store its connection string in the environment, never in source control.

```powershell
py -3.12 -m venv backend/venv
./backend/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
# Set DATABASE_URL and a randomly generated JWT_SECRET in your local environment.
# JWT_SECRET must contain at least 32 characters; use a cryptographically random value.
./backend/venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend reads environment variables directly; it does not automatically load .env files. Startup requires DATABASE_URL and JWT_SECRET. Before serving, one transaction creates all 18 tenant tables and enables + forces college-scoped RLS. Runtime roles able to bypass RLS are rejected. Schema creation is idempotent for the current schema; later schema changes need explicit migrations rather than relying on create_all.

Startup also runs seed.py idempotently, creating 4,800 named synthetic profiles, 45 companies and simulated drives in Demo College 1. Their generated passwords are not shared and seed accounts are not public demo logins. Running the script again preserves existing profiles.

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1
```

Set VITE_API_URL=/api for local development. Vite proxies /api to http://127.0.0.1:8000, keeping local browser requests on the frontend origin. Production VITE_API_URL remains the absolute Render URL; production CORS permits only https://jobjugaad.vercel.app. All backend calls go through frontend/src/api. JWTs expire after two hours and are stored in sessionStorage for the current tab; logout clears the browser token. There is no refresh-token, email-verification, password-reset, or immediate server-side logout revocation flow in this phase.

## Tenant enforcement

The original 17 tenant tables listed in [PHASE5_AUDIT.md](PHASE5_AUDIT.md), plus placement_model_profiles (18 total), carry college_id. Application queries include college filters; profile endpoints also require the JWT user to own the student row. Every table has ENABLE and FORCE ROW LEVEL SECURITY with both USING and WITH CHECK scoped to transaction-local app.college_id. Transaction completion clears that setting before connection reuse. Composite foreign keys prevent linking children to a student in a different college.

RLS is the second tenant enforcement layer, not a replacement for application authorization. The runtime role owns the initial schema for startup DDL; FORCE RLS ensures normal owner queries are still restricted. Future production deployment should separate migrations from the runtime role.

## Verification

Against a local PostgreSQL instance and a non-bypass application role:

```powershell
# Configure DATABASE_URL for an isolated localhost test database and JWT_SECRET first.
$env:ALLOW_TEST_DATABASE = 'yes'
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
./backend/venv/Scripts/python.exe -m unittest discover -s backend/tests -v
npm --prefix frontend run build
```

Tests create synthetic test records only in an explicitly enabled localhost database and leave those records in place. They cover JWT claims/hash verification, tampered/expired tokens, role escalation, own-profile restrictions, all-table RLS without application filters, denied cross-tenant writes/links, tenant context reset, resume extraction/persistence/rejection, score boundaries, and seed idempotence/count. These are correctness checks, not an accuracy benchmark. All 14 test cases passed on 2026-09-22.

Swagger signup, login, current identity, profile retrieval/update, readiness, and PDF upload were exercised locally before frontend integration. A synthetic PDF fixture is generated by the test helper; never use a real student's resume for automated checks.

## Deploy

Render: existing free Python service jobjugaad-api, root backend/, build pip install -r requirements.txt, start uvicorn main:app --host 0.0.0.0 --port $PORT, health /health. Set DATABASE_URL to the managed database's internal URL and JWT_SECRET to a strong randomly generated secret in Render's Environment settings. Never set JWT_SECRET or DATABASE_URL in Vercel.

The existing Oregon database Job-Jugaad expires on **2026-10-21** under its free plan. Existing external IP rules are unchanged. render.yaml is a fresh-environment template, not the configuration mechanism used for the existing live services.

Vercel: root frontend/, Vite, build npm run build, output dist. Include source files outside the root directory so the supplied assets/ logos are available. VITE_API_URL=https://jobjugaad-api.onrender.com is embedded at build time. The SPA fallback supports direct login/profile URLs.

CORS permits exactly https://jobjugaad.vercel.app with explicit GET/POST/PUT/OPTIONS methods and Authorization/Content-Type headers; no cookies or wildcard configuration. Resume parsing accepts up to 5 MB, 20 pages, and 200,000 extracted characters, with a 20-second subprocess timeout. Scanned/encrypted/unreadable PDFs return a readable error. The raw PDF is not persisted.

Placement support uses simple thresholds. A trained support classifier, mock interview, live chatbot, embedding libraries and pgvector are not implemented. A separate public-data placement classifier now has its own academic-input form and explained signal alongside weighted readiness. Jugaad Dost is a static FAQ.


## Phase 3 administrator setup

The Command Center is available at `/admin` after logging in with an allowlisted account. Register the intended account through the normal signup first. In the backend environment, set `ADMIN_ACCOUNTS` to a JSON array such as `[{"email":"admin@example.test","college_id":1}]`, using the exact existing account and demo college. Do not commit real account details or passwords. Startup promotes the selected account; log in again after deployment. No public admin signup or default admin password exists. Removing an allowlist entry denies subsequent admin logins and requests.

Phase 3 adds deterministic scheduling proposals with explicit admin approval, branch/skill **shortlist** conversion charts, advertised package statistics and rule-based placement support review. Phase 4 adds an accepted-offer placement proxy with separately recorded joining. Support scores count three proposed indicators and always include factors, explanations and interventions; they are not risk probabilities. See `ARCHITECTURE.md` Section 5 for exact thresholds and scheduling semantics.

For the synthetic demo, open Scheduling to inspect the deliberately imported overlap, propose a resolution and approve it with a reason. Open Placement support and select Simulated Cloud Support Track to inspect the support evidence. Resolved fixtures are not recreated on restart. Phase 3 live/browser verification status is tracked in `MEMORY.md`; Phase 4 is authorized; its live verification status is tracked there too.


## Phase 4 offers and notifications

Students open **My offers** to inspect letter, documents, verification, acceptance and joining separately. Administrators open **Command Center → Offers**, choose a selected interview and create a draft; issue the letter before the student records a response. Students exchange documents through the college's agreed external channel and record submission here. Administrators verify externally and record verification before joining. Reasons and before/after stages remain in history; stale concurrent changes are rejected.

**Notifications** is a recipient-scoped simulated feed. Interview and offer actions create in-app records; no email/SMS is sent. Offer records are paginated and synthetic examples are labeled. Accepted-offer statistics include synthetic records and do not prove joining; joining has its own count.

Startup expands the idempotent demo to 4,800 synthetic students and 45 companies. Shared preparation plus noise creates correlated profiles/outcomes; these are proposed generation assumptions, not real placement data. Matching demonstrations retain the original three drives; the evaluation considers 13 simulated roles.

Frozen expectations and limitations: [protocol](EVALUATION_PROTOCOL.md). Actual results and disagreements: [written report](evaluations/phase4-report.md) and [full evidence](evaluations/phase4-results.json). Matching reproduced 25/30 expected roles; readiness bands and support flags agreed on 10/10 each. These counts describe an assistant-authored synthetic sanity check against our own assumptions, never validated accuracy.


### Verified live Phase 4 walkthrough — 2026-09-23

Use the existing **Synthetic Phase 4 Lifecycle Check** student and **Synthetic Phase 4 Lifecycle Drive** in Demo College 1; avoid creating duplicate fixtures. Profiling, matching evidence, student-owned offer/feed access and denial of admin-only access have been checked through the live API. The user subsequently completed the administrator walkthrough, with student API checks performed by the agent.

1. In Scheduling, verify the correct student's booking is approved. After its scheduled end, record **Selected** with a synthetic-test reason.
2. In Offers, find that selected interview, create a draft and record **letter issued**.
3. From the owning synthetic student account, record **acceptance** and **documents submitted**. This declares external document exchange; there is no document upload/automatic verification feature.
4. From the administrator account, record **verified**, then **joined**, with reasons.
5. Check all five stages, audit history, the student/admin notification feeds and the changed accepted/joined analytics. Notifications are in-app only.

The live sequence completed for student 4805 / drive 17 / interview 7556 / offer 2385. All five final stages and six offer audit actions were verified through the student API, along with nine recipient notifications and idempotent read state. The user supplied refreshed admin analytics: 1,418 students with active accepted offers, 701 recorded joined and 2,385 offers, including 2,383 seeded synthetic offers. Manually created test records are fictional too and are disclosed by their names/reasons; the seed marker does not make other records validated real placements. Browser automation remained unavailable: admin UI actions/counts are user-verified, while student actions were API-verified. Thirty-four local checks and production builds passed. The user accepted Phase 4 end to end and authorized Phase 5. Credentials are not included in the repository.

## Final demo and honest scope

Follow [DEMO_GUIDE.md](DEMO_GUIDE.md) for the exact Profiling → Matching → Scheduling → Offer → Analytics clicks, named fixtures and fresh-run alternative. [JUDGE_REVIEW.md](JUDGE_REVIEW.md) provides implementation-grounded answers; the written scalability statement is in [Architecture Section 9](ARCHITECTURE.md#9-dataset--evaluation). Competing campus placement platforms exist; no first-mover claim is made. The workflow demonstration dataset remains synthetic and weighted scores remain proposed rules; the separate placement signal is backed by a trained public-data classifier. Notifications never deliver email/SMS and document stages are human declarations. Self-selected enrollment, schema-owner runtime privileges, missing rate limiting and absent production backup/migration workflows remain hardening work.

Phase 5 release `c3d7a57` serves API 0.6.0. All 17 actual live tenant policies were verified on 2026-09-23, along with allowed/rejected CORS responses and protected-route authentication. All 37 checks passed across regression/retest; the final production build and explained-score component rendering passed. The [per-table/per-screen audit](PHASE5_AUDIT.md) distinguishes these checks from the presenter's remaining browser rehearsal.

## Hybrid real + synthetic data

Campus Recruitment (`backend/data/Placement_Data_Full_Class.csv`, Ben Roshan/Kaggle via a pinned public GitHub mirror) trains a separate **Placement Likelihood Model** from real/public labels. Its original collection is publisher-reported, not independently audited. It contains no skill/project/certification/resume evidence, so the existing 4,800-student workflow demo and matching evaluation remain synthetic. Weighted readiness and support rules are unchanged.

Accuracy **88.37%**, precision **93.10%**, recall **90.00%**, F1 **91.53%** (positive class: Placed; **43 held-out records**, 172 training, 215 total). Confusion matrix, with actual rows / predicted columns ordered Not Placed then Placed: `[[11, 2], [3, 27]]`. These are measured internal held-out results, not a synthetic sanity check and not a claim of production-grade or BPUT accuracy. The persisted forest is trained on 172 records, not all 215; its probabilities are uncalibrated. [Evaluation and limits](backend/ml/EVALUATION.md) · [Reproduce training](backend/ml/README.md) · [Source/license](backend/data/README.md).

**Integration:** the user reviewed metrics and authorized deployment. Student profile → Placement Likelihood Model → Add or edit academic model inputs collects the 12 optional compatible fields. The API loads the saved model once at startup, with checksum and pinned-version checks; it never trains on a request. Missing records produce no score. Available signals show the baseline, all 12 local contributions and an explanation alongside a separately labeled Weighted Readiness Score. The new placement_model_profiles table has application college filters, ownership checks and ENABLE/FORCE RLS. Public source rows are not turned into fictional tenant accounts. See [integration verification and demo steps](evaluations/placement-integration.md) for release evidence.

**Public-model deployment verified 2026-09-24:** release e6eba59, API 0.7.0, model ready on Render, all 18 actual tenant policies verified, owned-profile inference/persistence and missing-input behavior passed, Vercel production bundle verified. See [safe live evidence](evaluations/placement-live-security.json). Interactive browser automation remains unavailable; API/component rendering checks are not presented as a click-through test.
