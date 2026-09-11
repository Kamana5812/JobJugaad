# JobJugaad — Project Memory

Living record of project state and decisions. Update this file whenever a major decision is made or a phase completes — this is the single source of truth for "where things stand," especially useful for onboarding teammates or resuming work with an AI coding assistant.

**Last updated:** _(update this line every time you edit this file)_
**Current phase:** Phase 0 — Environment & Skeleton (not yet started)

---

## 1. Project Identity

- **Name:** JobJugaad
- **Event:** BPUT Hackathon 2026, Problem Statement 10 (official title: "CampusLink — AI-Powered Campus-to-Corporate Placement Management & Analytics Platform")
- **Tagline:** "Placement ka Jugaad, AI ke Saath."
- **Repo:** _(add GitHub URL once created)_
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

_Add a new row every time a meaningful architectural or product decision is made._

---

## 3. Current State

### ✅ Completed
- [ ] _(nothing yet — update as phases complete)_

### 🚧 In Progress
- [ ] _(update as work starts)_

### ⏭️ Next Up
- Phase 0 tasks — see `PHASES.md`

---

## 4. Known Limitations / Honest Caveats

Keep this section current — it's exactly what a judge or mentor will ask about, and it's better to know your own gaps than be caught off guard.

- Matching and readiness scoring are rule-based (weighted sums / keyword matching) for the MVP, not a trained ML model — documented deliberately for explainability (see `RULES.md` §6).
- Notifications are simulated in-app only; no real email/SMS/WhatsApp delivery.
- Multi-college support is designed into the schema (`college_id`) but only tested with a single synthetic college's data.
- Render's free tier cold-starts after 15 minutes idle — must warm up before live demos.
- Simulator (P2) projections are generated from the synthetic dataset's conversion model, not real historical placement data.

---

## 5. Open Questions

_Track unresolved questions here so they don't get lost between sessions._

- [ ] Final call on TypeScript vs. plain JavaScript for the frontend?
- [ ] Do we attempt the pgvector semantic-matching stretch goal, or stop at keyword matching?
- [ ] Who owns seed data generation (the `seed.py` script) and when does it get finalized?

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

> _(example format)_
> **Session ended:** [date]
> **What I just finished:** ...
> **What's broken/incomplete:** ...
> **What to do next:** ...
