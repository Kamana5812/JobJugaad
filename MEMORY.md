# JobJugaad — Project Memory

Living record of project state and decisions. Update this file whenever a major decision is made or a phase completes — this is the single source of truth for "where things stand," especially useful for onboarding teammates or resuming work with an AI coding assistant.

**Last updated:** 2026-09-11
**Current phase:** Phase 0 — Environment & Skeleton (completed)

---

## 1. Project Identity

- **Name:** JobJugaad
- **Event:** BPUT Hackathon 2026, Problem Statement 10 (official title: "CampusLink — AI-Powered Campus-to-Corporate Placement Management & Analytics Platform")
- **Tagline:** "Placement ka Jugaad, AI ke Saath."
- **Repo:** https://github.com/Kamana5812/JobJugaad
- **Live URLs:** Frontend: https://job-jugaad-sepia.vercel.app/ · Backend: https://jobjugaad-lmca.onrender.com

---

## 2. Key Decisions Log

| Date | Decision | Reason |
|---|---|---|
| 2026-09-11 | Stack: React + Tailwind (frontend), FastAPI (backend), PostgreSQL (DB) | Free-tier deployable on Vercel + Render; matches team's existing React/JS skills |
| 2026-09-11 | Rule-based scoring for MVP, not black-box ML | Problem statement explicitly requires explainability; rule‑based is transparent and easy to justify to judges |
| 2026-09-11 | Deployment target: Vercel (frontend) + Render (backend + DB) | Both have generous free tiers, GitHub auto‑deploy, beginner‑friendly |
| 2026-09-11 | Synthetic dataset (~4,800 students, 40–50 companies), not real data | No real student/recruiter data available for a hackathon |
| 2026-09-11 | Brand palette: Navy / Saffron / Green / White | Indian identity that feels modern, not like tricolor kitsch — see `DESIGN.md` |
| 2026-09-11 | Readiness Score weighting: 30/20/15/15/10/10 (Technical/Projects/Academics/Aptitude/Communication/Interview) | Proposed implementation model — explicitly documented as not an official BPUT formula |
| 2026-09-11 | Live URLs set for Phase 0: Frontend https://job-jugaad-sepia.vercel.app/, Backend https://jobjugaad-lmca.onrender.com | Enables end‑to‑end demo of health‑check integration |
| 2026-09-11 | Phase 1 implementation (auth, student models, resume upload, readiness engine, UI) | Delivered JWT‑based auth, profile CRUD, PDF resume parsing, weighted readiness scoring, and protected React UI |

_Add a new row every time a meaningful architectural or product decision is made._

---

## 3. Current State

### ✅ Completed
- [x] Phase 0 — Environment & Skeleton (deployed, live URLs functional)

### 🚧 In Progress
- None

### ⏭️ Next Up
- Phase 1 — Student Core (see `PHASES.md`)

---

## 4. Known Limitations / Honest Caveats

Keep this section current — it's exactly what a judge or mentor will ask about, and it's better to know your own gaps than be caught off guard.

- Matching and readiness scoring are rule‑based (weighted sums / keyword matching) for the MVP, not a trained ML model — documented deliberately for explainability (see `RULES.md` §6).
- Notifications are simulated in‑app only; no real email/SMS/WhatsApp delivery.
- Multi‑college support is designed into the schema (`college_id`) but only tested with a single synthetic college's data.
- Render's free tier cold‑starts after 15 minutes idle — must warm up before live demos.
- Simulator (P2) projections are generated from the synthetic dataset's conversion model, not real historical placement data.

---

## 5. Open Questions

_Track unresolved questions here so they don't get lost between sessions._

- [ ] Final call on TypeScript vs. plain JavaScript for the frontend?
- [ ] Do we attempt the pgvector semantic‑matching stretch goal, or stop at keyword matching?
- [ ] Who owns seed data generation (`seed.py`) and when does it get finalized?

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

---

## 8. Session Handoff Notes

_When ending a work session, leave a short note here for whoever (or whatever AI agent) picks this up next._

> **Session ended:** 2026-09-11
> **What I just finished:** Phase 0 — Environment & Skeleton. Cleaned up previous future code and set up barebones React/Tailwind frontend and FastAPI backend with a /health endpoint.
> **What's broken/incomplete:** None for Phase 0.
> **What to do next:** Begin Phase 1 — Student Core (implement student auth, models, resume parsing, readiness engine, UI).