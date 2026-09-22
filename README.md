# JobJugaad

An **explainability-first** campus placement platform for BPUT Hackathon 2026's CampusLink problem statement.

Phase 0 was explicitly accepted on 2026-09-22. Phase 1 implements Student Core: student signup/login, editable profiles, PDF resume text extraction, and an explained readiness score. Phase 1 deployment verification is in progress; Phase 2 is not authorized.

- Frontend: [jobjugaad.vercel.app](https://jobjugaad.vercel.app)
- Backend: [health](https://jobjugaad-api.onrender.com/health) · [interactive API](https://jobjugaad-api.onrender.com/docs)
- Repository: [Kamana5812/JobJugaad](https://github.com/Kamana5812/JobJugaad)

## Student flow

Create a student account using synthetic details and Demo College 1 or 2. Use the same college when logging in. Upload a text-based resume PDF, review the extracted text, then record skills, projects, CGPA, and existing assessment results. Save to recalculate readiness. Every response and score display includes six factors and an explanation.

Enrollment is self-selected for this hackathon demo, not verification of real college membership. Student tokens cannot create recruiter/admin roles or access another student's profile, even within the same college. Do not use real student data until institution-controlled enrollment and operational hardening are implemented.

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

## Run locally (PowerShell)

Use Python 3.12, Node.js 24, and PostgreSQL. Create a database whose application role owns it but has neither superuser nor BYPASSRLS privileges. Store its connection string in the environment, never in source control.

```powershell
py -3.12 -m venv backend/venv
./backend/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
# Set DATABASE_URL and a randomly generated JWT_SECRET in your local environment.
# JWT_SECRET must contain at least 32 characters; use a cryptographically random value.
./backend/venv/Scripts/python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend reads environment variables directly; it does not automatically load .env files. Startup requires DATABASE_URL and JWT_SECRET. Before serving, one transaction creates all five tables and enables + forces college-scoped RLS. Runtime roles able to bypass RLS are rejected. Schema creation is idempotent for the initial Phase 1 schema; later schema changes need explicit migrations rather than relying on create_all.

Startup also runs seed.py idempotently, creating 50 named synthetic profiles in Demo College 1. Their generated passwords are not shared and seed accounts are not public demo logins. Running the script again preserves existing profiles.

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1
```

Set VITE_API_URL to your local API URL (default http://localhost:8000). All backend calls go through frontend/src/api. JWTs expire after two hours and are stored in sessionStorage for the current tab; logout clears the browser token. There is no refresh-token, email-verification, password-reset, or immediate server-side logout revocation flow in this phase.

## Tenant enforcement

users, students, student_skills, projects, and certifications each carry college_id. Application queries include college filters; profile endpoints also require the JWT user to own the student row. Every table has ENABLE and FORCE ROW LEVEL SECURITY with both USING and WITH CHECK scoped to transaction-local app.college_id. Transaction completion clears that setting before connection reuse. Composite foreign keys prevent linking children to a student in a different college.

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

Tests create synthetic test records only in an explicitly enabled localhost database and leave those records in place. They cover JWT claims/hash verification, tampered/expired tokens, role escalation, own-profile restrictions, all-table RLS without application filters, denied cross-tenant writes/links, tenant context reset, resume extraction/persistence/rejection, score boundaries, and seed idempotence/count. These are correctness checks, not an accuracy benchmark. All six test cases passed on 2026-09-22.

Swagger signup, login, current identity, profile retrieval/update, readiness, and PDF upload were exercised locally before frontend integration. A synthetic PDF fixture is generated by the test helper; never use a real student's resume for automated checks.

## Deploy

Render: existing free Python service jobjugaad-api, root backend/, build pip install -r requirements.txt, start uvicorn main:app --host 0.0.0.0 --port $PORT, health /health. Set DATABASE_URL to the managed database's internal URL and JWT_SECRET to a strong randomly generated secret in Render's Environment settings. Never set JWT_SECRET or DATABASE_URL in Vercel.

The existing Oregon database Job-Jugaad expires on **2026-10-21** under its free plan. Existing external IP rules are unchanged. render.yaml is a fresh-environment template, not the configuration mechanism used for the existing live services.

Vercel: root frontend/, Vite, build npm run build, output dist. Include source files outside the root directory so the supplied assets/ logos are available. VITE_API_URL=https://jobjugaad-api.onrender.com is embedded at build time. The SPA fallback supports direct login/profile URLs.

CORS remains wide open without cookies by the explicit Phase 0 instruction; restrict origins in Phase 5. Resume parsing accepts up to 5 MB, 20 pages, and 200,000 extracted characters, with a 20-second subprocess timeout. Scanned/encrypted/unreadable PDFs return a readable error. The raw PDF is not persisted.

No matching, placement support prediction, mock interview, live chatbot, embedding library, or pgvector feature is implemented. Jugaad Dost is a static FAQ.
