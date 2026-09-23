# JobJugaad — Project Rules

Conventions and guardrails for anyone (human or AI agent) working on this codebase. Read this before writing code.

---

## 1. General Principles

1. **A smaller working product beats a giant broken one.** Always keep `main` deployable.
2. **Explainability over cleverness.** Every score or ranking must show *why*, not just a number.
3. **Deploy early, deploy often.** The first commit should already be deployable (even as a "hello world" health check).
4. **No secrets in code.** API keys, DB URLs, and JWT secrets live only in environment variables (`.env` locally, dashboard vars in Vercel/Render). Never commit `.env`.
5. **Don't build P1/P2 before P0 works end-to-end.** Check `PHASES.md` before starting new work.

---

## 2. Git Workflow

- **Branches:** `main` (always deployable) + `feature/<short-name>` for in-progress work.
- **Commits:** small, descriptive, present tense. e.g. `add readiness score endpoint`, not `fixes`.
- **Never force-push to `main`.**
- **Merge to `main` only when the feature runs locally without errors.**
- Push to `main` early and often — Render/Vercel auto-deploy on push, so `main` is your live demo at all times.

---

## 3. Backend Rules (FastAPI / Python)

- One router file per domain: `routers/students.py`, `routers/recruiters.py`, `routers/admin.py`. Don't put unrelated endpoints in the same file.
- All request/response shapes go through Pydantic schemas in `schemas.py` — never return raw SQLAlchemy objects directly.
- Business logic (scoring, matching, scheduling) lives in `engines/`, not inline in route handlers. Routers should stay thin: validate → call engine → return.
- Every engine function must return a structure that includes **why**, e.g.:
  ```python
  {
    "score": 84,
    "band": "Ready",
    "breakdown": {"technical_skills": 91, "projects": 88, ...},
    "explanation": "Your technical skills and project experience are strong..."
  }
  ```
- Database access always goes through SQLAlchemy sessions — no raw SQL strings unless there's a documented reason.
- Every table query must filter by `college_id` (multi-tenancy — see `ARCHITECTURE.md`). This is the application-level layer; a PostgreSQL Row-Level Security policy on every multi-tenant table is the required second layer beneath it — don't rely on application code alone to prevent cross-college data leaks.
- Use environment variables for `DATABASE_URL` and `JWT_SECRET` — read via `os.environ.get(...)`, never hardcoded.
- Run `pip freeze > requirements.txt` after installing any new package, and commit the updated file — Render's build depends on it.

---

## 4. Frontend Rules (React)

- One folder per portal under `pages/`: `student/`, `recruiter/`, `admin/`. Don't mix portal-specific components across folders.
- Shared UI (cards, pills, tables, chart wrappers) goes in `components/` and must be reusable across portals.
- All backend calls go through `api/` wrapper functions — no raw `axios.get(...)` calls scattered inside components.
- Never hardcode the backend URL — always use `import.meta.env.VITE_API_URL`.
- Every page that displays a score or ranking must render the explanation/breakdown, not just the number — this is a product requirement, not a nice-to-have.
- Use Tailwind utility classes; avoid custom CSS files unless Tailwind genuinely can't express the style.
- Keep components small — if a page file exceeds ~200 lines, extract sub-components.

---

## 5. API Conventions

- REST-style, resource-based paths: `/students/{id}/readiness`, not `/getStudentReadiness`.
- Use plural nouns for collections: `/students`, `/drives`, `/offers`.
- Every authenticated endpoint expects `Authorization: Bearer <token>` and validates role before returning data.
- Error responses always return `{"detail": "human-readable message"}` with an appropriate HTTP status code (400/401/403/404/500) — never a bare 500 with no message.

---

## 6. Data & AI Rules

- **Never claim a rule-based score is a trained ML model.** Document actual logic honestly in code comments and in `ARCHITECTURE.md` — judges will ask (see `JUDGE_REVIEW.md`).
- Any weighting scheme (e.g. readiness formula) must be clearly labeled as a **proposed implementation**, not a fixed external standard.
- Synthetic data generation lives in one script (`seed.py`) — don't hand-write JSON fixtures scattered across the codebase.
- Any number presented in a demo (e.g. simulator projections) must come from the actual synthetic dataset/model — never a hardcoded fictional number in the UI.
- **Never fabricate an accuracy, benchmark, or performance number.** If asked for one and no real evaluation has been run, say so and define the evaluation protocol instead (see `ARCHITECTURE.md` §9) — this applies to code comments, UI copy, and spoken pitch material equally.
- **The Explanation Generator is template-based, never an LLM call.** An LLM can hallucinate an incorrect reason for a score, which is worse than no explanation at all. The only place an LLM use is justified anywhere in this system is free-text resume section extraction — nowhere else.
- **If an At-Risk classifier goes beyond P0 rule-based thresholds, class imbalance must be handled** (SMOTE or class weighting) before it ships. Students needing support are always a minority class; an untreated classifier will silently predict "no support needed" for nearly everyone while looking falsely accurate. See `ARCHITECTURE.md` §5, Layer 5 (Predictive Analytics).
- **Scope discipline:** do not build the AI Mock Interview feature — the competitive space is saturated with 10+ mature dedicated products, and a hackathon version cannot compete. "Jugaad Dost" (AI Career Chatbot) ships only as a static UI label / FAQ panel, never as a built LLM-backed chatbot.

---

## 6b. Responsible Language Rules

These apply everywhere the product speaks to a user — UI copy, API response messages, pitch material, and documentation alike.

- **Never say an AI "understands" or "completely knows" a student.** Use "rule-based, structured view of the student's profile" for this implementation; no trained model is present.
- **Never label a student outcome as "at risk" without qualification, and never imply failure.** The correct framing is: "a student who may require additional placement support based on measurable indicators." Support categories (Technical / Aptitude / Communication / Resume-Profile / Mentoring) are always preferred over a single risk label.
- **Never present a rejection as a dead end.** Every "not eligible" or "below threshold" output must be paired with the specific gap and, where feasible, a suggested next step — per the "Reject Less → Identify the Gap → Help Improve" philosophy in `PRD.md` §1.
- **Never claim an academic-performance ranking is fair to all recruiters' priorities.** Different recruiters weight academics, skills, projects, certifications, and communication differently — never hardcode CGPA as the dominant or sole ranking factor; the weighting must remain configurable per role.
- **Never claim full autonomous decision-making.** Scheduling conflict resolutions, matching shortlists, and support-priority flags are always framed as suggestions pending human (admin/recruiter) approval — never as a final, unreviewable action.
- **Never make an absolute security or privacy claim.** No "100% secure," "military-grade," or "zero risk" language anywhere — state only what is actually implemented (JWT + RBAC + RLS + least-privilege access).
- **Never overclaim long-term tracking.** Post-joining career outcome tracking is described as a planned/future capability unless it is actually implemented in the working prototype — see `ARCHITECTURE.md` §5, Layer 6 for the specific case (before/after readiness tracking).

---

## 7. Do's and Don'ts

**Do**
- Test every new endpoint via `/docs` (FastAPI's auto-generated page) before wiring the frontend to it.
- Keep `MEMORY.md` updated with major decisions and current state.
- Write the explanation string for every score-producing feature before considering it "done."

**Don't**
- Don't add a new npm/pip package without a clear reason — every dependency is something to explain if asked.
- Don't build the P2 Simulator before P0's matching and scheduling work end-to-end. Don't build AI Mock Interview at all. Don't build "Jugaad Dost" as a real chatbot — label only.
- Don't leave `allow_origins=["*"]` in CORS config for the final deployed version — lock it to the real Vercel URL.
- Don't commit `.env`, `venv/`, or `node_modules/` — ensure `.gitignore` covers all three from day one.

---

## 8. Definition of Done (per feature)

A feature is "done" only when:
1. It works locally against the real database (not mocked data).
2. It's deployed and works on the live Vercel + Render URLs.
3. Any score/ranking it produces includes a human-readable explanation.
4. It's reflected in `MEMORY.md` under "Completed."
