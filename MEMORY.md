# JobJugaad — Project Memory

Living record of project state and decisions. Update this file whenever a major decision is made or a phase completes — this is the single source of truth for "where things stand," especially useful for onboarding teammates or resuming work with an AI coding assistant.

**Last updated:** 2026-09-21
**Current phase:** Phase 0 — Environment & Skeleton (local skeleton verified; deployment and user confirmation pending)

---

## 1. Project Identity

- **Name:** JobJugaad
- **Event:** BPUT Hackathon 2026, Problem Statement 10 (official title: "CampusLink — AI-Powered Campus-to-Corporate Placement Management & Analytics Platform")
- **Tagline:** "Placement ka Jugaad, AI ke Saath."
- **Repo:** https://github.com/Kamana5812/JobJugaad (existing public repository; initial push pending)
- **Live URLs:** Frontend: _(pending)_ · Backend: _(pending)_

---

## 2. Key Decisions Log

| Date | Decision | Reason |
|---|---|---|
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
| 2026-09-21 | Use a Render Blueprint to link the managed PostgreSQL connection string; keep CORS open temporarily without credential support | Implements the user's explicit Phase 0 instructions. Restrict CORS in Phase 5. No multi-tenant tables are created before Phase 1. |
| 2026-09-21 | Reuse the existing public Kamana5812/JobJugaad repository | GitHub already has this name; preserve the user's existing repository and visibility rather than create a duplicate or change settings. |

_Add a new row every time a meaningful architectural or product decision is made._

---

## 3. Current State

### ✅ Completed
- [x] Imported both user-supplied brand assets and verified PNG format and dimensions: horizontal 1600 × 533; poster 1254 × 1254. No build phase is complete yet.
- [x] Created the architecture's frontend portal/API/component/context folders and backend engine/router folders, with later-phase modules left unimplemented.
- [x] Created `backend/venv` using bundled Python 3.12.14, installed all nine requested packages, and saved the exact `pip freeze` output in `backend/requirements.txt`; `pip check` passed.
- [x] Implemented and locally verified `/health`, its Pydantic response contract, open Phase 0 CORS, `/docs`, and the OpenAPI schema. Executed `/health` through Swagger UI with HTTP 200.
- [x] Built the React/Vite/Tailwind landing page with both supplied logos; verified the production preview calls the backend and the retry button works. Local PostgreSQL is correctly shown as not configured.
- [x] Added `.gitignore`, safe environment examples, deployment configuration, and README instructions; verified that virtual environments, node_modules, and `.env` files are ignored.

### 🚧 In Progress
- [ ] Commit and push the Phase 0 skeleton to the existing GitHub repository.
- [ ] Deploy Render backend and managed PostgreSQL, then deploy Vercel frontend with the live backend URL.

### ⏭️ Next Up
- Complete Phase 0 deployment, verify both live URLs and database connectivity, and obtain the user's explicit confirmation.
- Phase 1 is not authorized until Phase 0's Definition of Done is explicitly confirmed by the user.

---

## 4. Known Limitations / Honest Caveats

Keep this section current — it's exactly what a judge or mentor will ask about, and it's better to know your own gaps than be caught off guard.

- Matching and readiness scoring are rule-based (weighted sums / keyword matching) for the MVP, not a trained ML model — documented deliberately for explainability (see `RULES.md` §6).
- No engines or evaluation checks exist yet. Matching's synthetic sanity check and scoring's face-validity review are planned for Phase 4; no real-world accuracy is claimed.
- Notifications are planned as simulated in-app only; they are not implemented in Phase 0.
- Multi-college support (`college_id` filtering + Row-Level Security) is a required future implementation; no tenant tables or isolation tests exist yet.
- Local backend verification does not validate PostgreSQL: `DATABASE_URL` is not configured locally, and the managed database still needs provisioning.
- CORS currently permits all origins by explicit Phase 0 instruction; it must be restricted in Phase 5.
- Render's free tier cold-starts after 15 minutes idle — must warm up before live demos.
- Simulator (P2) projections are generated from the synthetic dataset's conversion model, not real historical placement data — a hypothetical demonstration, not a forecast.
- This is not the first AI-powered campus placement platform (8+ commercial competitors and one close open-source analogue, SkillBridge, exist) — differentiation rests specifically on explainable matching, placement-specific (responsibly-framed) support prediction, and the what-if simulator, not on the general category. See `RESEARCH_AUDIT.md` for the full competitive picture.
- AI Mock Interview is out of scope by decision, not by oversight. "Jugaad Dost" is a static label/FAQ panel, not a live chatbot, by decision.

---

## 5. Open Questions

_Track unresolved questions here so they don't get lost between sessions._

- [x] Use plain JavaScript for the frontend (Phase 0 decision).
- [ ] Do we attempt the pgvector semantic-matching stretch goal, or stop at keyword matching? (Default per `ARCHITECTURE.md`: stop at keyword matching for P0/P1, attempt only if time remains.)
- [ ] Who owns seed data generation (the `seed.py` script) and when does it get finalized?
- [ ] Do we attempt the Random Forest upgrade to the Readiness Engine using the public Kaggle dataset, or stay with the weighted rule for the whole hackathon?

---

## 6. Environment & Access Notes

_Do not put actual secret values here — only where to find them._

- `DATABASE_URL` — set in Render dashboard (Web Service → Environment) and locally in `backend/.env`
- `JWT_SECRET` — set in Render dashboard; generate a strong random string, never reuse across environments
- `VITE_API_URL` — set in Vercel project settings (Environment Variables) and locally in `frontend/.env`

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
