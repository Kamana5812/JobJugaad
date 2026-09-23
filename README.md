# JobJugaad

An **explainability-first** campus placement platform for BPUT Hackathon 2026's CampusLink problem statement.

Phase 0 was explicitly accepted on 2026-09-22. Phase 1 Student Core is deployed and verified: student signup/login, editable profiles, PDF resume text extraction, and an explained readiness score. Its live Definition of Done was demonstrated and accepted on 2026-09-22, including the user's independent RLS test. Phase 2 Talent Finder is deployed and verified; user acceptance is pending before Phase 3.

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

No accuracy benchmark or real-world outcome validation has been performed. Phase 4's planned face-validity review remains pending.

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

These are actual live outputs before manual smoke-test overrides: 300 seeded students plus one earlier synthetic check profile. They are **not accuracy or benchmark claims**. The self-labeled matching sanity evaluation remains scheduled for Phase 4. Seed-company passwords are unshared; create drives under your own recruiter account to run the same workflow.

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

The backend reads environment variables directly; it does not automatically load .env files. Startup requires DATABASE_URL and JWT_SECRET. Before serving, one transaction creates all nine tenant tables and enables + forces college-scoped RLS. Runtime roles able to bypass RLS are rejected. Schema creation is idempotent for the current Phase 1/2 schema; later schema changes need explicit migrations rather than relying on create_all.

Startup also runs seed.py idempotently, creating 300 named synthetic profiles, 12 companies and three simulated drives in Demo College 1. Their generated passwords are not shared and seed accounts are not public demo logins. Running the script again preserves existing profiles.

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1
```

Set VITE_API_URL to your local API URL (default http://localhost:8000). All backend calls go through frontend/src/api. JWTs expire after two hours and are stored in sessionStorage for the current tab; logout clears the browser token. There is no refresh-token, email-verification, password-reset, or immediate server-side logout revocation flow in this phase.

## Tenant enforcement

users, students, student_skills, projects, certifications, companies, jobs, matches, and match_overrides each carry college_id. Application queries include college filters; profile endpoints also require the JWT user to own the student row. Every table has ENABLE and FORCE ROW LEVEL SECURITY with both USING and WITH CHECK scoped to transaction-local app.college_id. Transaction completion clears that setting before connection reuse. Composite foreign keys prevent linking children to a student in a different college.

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

CORS remains wide open without cookies by the explicit Phase 0 instruction; restrict origins in Phase 5. Resume parsing accepts up to 5 MB, 20 pages, and 200,000 extracted characters, with a 20-second subprocess timeout. Scanned/encrypted/unreadable PDFs return a readable error. The raw PDF is not persisted.

Placement support prediction, mock interview, live chatbot, embedding libraries, and pgvector are not implemented. Jugaad Dost is a static FAQ.


## Phase 3 administrator setup

The Command Center is available at `/admin` after logging in with an allowlisted account. Register the intended account through the normal signup first. In the backend environment, set `ADMIN_ACCOUNTS` to a JSON array such as `[{"email":"admin@example.test","college_id":1}]`, using the exact existing account and demo college. Do not commit real account details or passwords. Startup promotes the selected account; log in again after deployment. No public admin signup or default admin password exists. Removing an allowlist entry denies subsequent admin logins and requests.

Phase 3 adds deterministic scheduling proposals with explicit admin approval, branch/skill **shortlist** conversion charts, advertised package statistics and rule-based placement support review. Placement percentage remains unavailable until offers are tracked. Support scores count three proposed indicators and always include factors, explanations and interventions; they are not risk probabilities. See `ARCHITECTURE.md` Section 5 for exact thresholds and scheduling semantics.

For the synthetic demo, open Scheduling to inspect the deliberately imported overlap, propose a resolution and approve it with a reason. Open Placement support and select Simulated Cloud Support Track to inspect the support evidence. Resolved fixtures are not recreated on restart. Phase 3 live/browser verification status is tracked in `MEMORY.md`; Phase 4 remains gated.
