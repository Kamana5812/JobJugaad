# JobJugaad — Project Memory

Living record of project state and decisions. Update this file whenever a major decision is made or a phase completes — this is the single source of truth for "where things stand," especially useful for onboarding teammates or resuming work with an AI coding assistant.

**Last updated:** _(update this line every time you edit this file)_
**Current phase:** Phase 1 — Student Core (in progress)

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
| — | Positioning reframed from "AI-powered" to "explainability-first" | Competitive/research review (`RESEARCH_AUDIT.md`) confirmed most of the system is deliberately rule-based, not ML — leading with "AI-powered" was vulnerable to the judge question "why is AI required?" |
| — | AI Mock Interview dropped from roadmap entirely; AI Career Chatbot demoted to static UI label only | 10+ mature dedicated competitors found for mock interview; a near-identical academic chatbot prototype (Campus-Connect) already exists — building either adds effort with zero differentiation (`TECHNICAL_VALIDATION.md` Phase 10) |
| — | Added PostgreSQL Row-Level Security as a second multi-tenancy enforcement layer beneath application-level `college_id` filtering | Confirmed as a real, implemented pattern via direct inspection of a comparable project (`codeecoffee/SmartCampus`) — stronger answer to "how is student privacy protected?" |
| — | Cited `Placement_Data_Full_Class.csv` (Kaggle) by name as the recommended real dataset anchor for Readiness Engine weight validation | Confirmed as the same dataset independently used across 5+ public student projects (`RESEARCH_AUDIT.md` Phase 6 addendum) |
| — | Jugaad Simulator repositioned as "applying an established workforce-planning technique to an underserved category," not an invention | "What-if scenario simulation" is a known HR analytics pattern (SAP/MiHCM); the innovation is the application to campus placement, not the technique itself |

_Add a new row every time a meaningful architectural or product decision is made._

---

## 3. Current State

### ✅ Completed
- [x] Phase 0 — Environment & Skeleton (deployed health endpoint, live URLs confirmed)

### 🚧 In Progress
- [ ] _(update as work starts)_

### ⏭️ Next Up
- Phase 1 — Student Core (in progress)

---

## 4. Known Limitations / Honest Caveats

Keep this section current — it's exactly what a judge or mentor will ask about, and it's better to know your own gaps than be caught off guard.

- Matching and readiness scoring are rule-based (weighted sums / keyword matching) for the MVP, not a trained ML model — documented deliberately for explainability (see `RULES.md` §6).
- No real-world accuracy has been (or currently can be) validated for the Matching Engine, absent real hiring outcome data — only a synthetic sanity check exists, and it is labeled as such everywhere it appears.
- Notifications are simulated in-app only; no real email/SMS/WhatsApp delivery.
- Multi-college support is designed into the schema (`college_id` + Row-Level Security) but only tested with a single synthetic college's data.
- Render's free tier cold-starts after 15 minutes idle — must warm up before live demos.
- Simulator (P2) projections are generated from the synthetic dataset's conversion model, not real historical placement data — a hypothetical demonstration, not a forecast.
- This is not the first AI-powered campus placement platform (8+ commercial competitors and one close open-source analogue, SkillBridge, exist) — differentiation rests specifically on explainable matching, placement-specific at-risk prediction, and the what-if simulator, not on the general category. See `RESEARCH_AUDIT.md` for the full competitive picture.
- AI Mock Interview is out of scope by decision, not by oversight. "Jugaad Dost" is a static label/FAQ panel, not a live chatbot, by decision.

---

## 5. Open Questions

_Track unresolved questions here so they don't get lost between sessions._

- [ ] Final call on TypeScript vs. plain JavaScript for the frontend?
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
