# JobJugaad — Build Phases

Build order for the hackathon. Each phase should end with something deployed and demoable — never work for a full day without pushing to `main`.

---

## Phase 0 — Environment & Skeleton (Day 1)

**Goal:** An empty but fully deployed pipeline, end to end.

- [ ] Install Node.js, Python, Git, VS Code; create GitHub repo `jobjugaad`
- [x] Create `frontend/` (Vite + React + Tailwind) and `backend/` (FastAPI) folders
- [x] Backend: minimal `main.py` with a `/health` endpoint
- [x] Frontend: minimal landing page hitting `/health` and displaying the result
- [x] Push to GitHub
- [x] Deploy backend to Render (Web Service, free tier)
- [x] Create Render Managed PostgreSQL instance, connect `DATABASE_URL` — reused the existing `Job-Jugaad` instance
- [x] Deploy frontend to Vercel, set `VITE_API_URL` to the live Render URL
- [x] Confirm: opening the Vercel URL shows a successful call to the live backend — agent verified; user acceptance pending

**Definition of done:** A live URL exists and works, even though it does nothing useful yet.

**Deployment verified 2026-09-21:** https://jobjugaad.vercel.app → https://jobjugaad-api.onrender.com/health → PostgreSQL connected. **Awaiting the user's explicit confirmation before Phase 1.**

---

## Phase 1 — Student Core (Day 2)

**Goal:** Career Copilot MVP — profile in, readiness score out.

- [ ] Database models: `users`, `students`, `student_skills`, `projects`, `certifications`
- [ ] Auth: signup/login endpoints, JWT issuance, password hashing
- [ ] Resume upload endpoint (PDF → text extraction via pdfplumber)
- [ ] Readiness Engine: weighted score calculation + band mapping (Not Ready → Highly Employable) + explanation string
- [ ] Frontend: student signup/login, profile page, resume upload, readiness score display with breakdown
- [ ] Seed script: generate ~50 synthetic student profiles for testing

**Definition of done:** A student can sign up, upload a resume, and see a readiness score with an explanation — live on Vercel.

---

## Phase 2 — Recruiter Core & Matching (Day 3)

**Goal:** Talent Finder MVP — post a job, get an explainable ranked list.

- [ ] Database models: `companies`, `jobs`, `matches`
- [ ] Recruiter signup/login, company profile creation
- [ ] Drive/job creation endpoint (CTC, min CGPA, eligible branches, required skills)
- [ ] Skill Gap Engine: compare student proficiency vs. target role requirements
- [ ] Matching Engine: eligibility filter → skill match → weighted score → factor breakdown → explanation (must match the official "Below Threshold: ..." format for rejections)
- [ ] Frontend: recruiter drive creation form, "Run AI Matching" button, ranked candidate list with score breakdown
- [ ] Expand seed data to ~200–500 students and 10–15 companies

**Definition of done:** A recruiter can create a drive, run matching, and see a ranked, explainable shortlist — live on Vercel. Demonstrated against **at least 3 simulated drives** (official deliverable requirement).

---

## Phase 3 — Scheduling & Admin Analytics (Day 4)

**Goal:** Placement Command Center MVP — conflict-free scheduling and a live dashboard.

- [ ] Database models: `schedules`, `interviews`
- [ ] Scheduling Engine: conflict detection (student/venue/panel overlap) + next-free-slot suggestion
- [ ] Admin analytics endpoint: totals (students, placement %, recruiters, drives), branch/skill conversion, package stats
- [ ] Frontend: admin dashboard with conflict alerts and analytics charts (Recharts)
- [ ] Placement Support Engine: **rule-based thresholds only for this phase** (e.g. 3+ skill gaps AND low mock score AND low activity). Output is a support priority + named contributing factors, never a "will fail"-style verdict. Do not build a trained classifier yet — if upgraded later, class imbalance must be handled via SMOTE or class weighting first, per `ARCHITECTURE.md` §5, or the model will silently predict "no support needed" for nearly everyone

**Definition of done:** Admin can see a live dashboard, trigger a scheduling conflict, watch it get resolved (pending admin approval), and see students who may need additional support flagged with named factors — all live.

---

## Phase 4 — Offers, Notifications & Data Polish (Day 5)

**Goal:** Complete the lifecycle past "Selected."

- [ ] Database model: `offers` (offer letter, documents, verification, acceptance, joining status)
- [ ] Offer tracking endpoints + frontend views (student and admin sides)
- [ ] Simulated notification engine (in-app notification feed; no real email/SMS needed)
- [ ] Expand and finalize synthetic dataset (~4,800 students, 40–50 companies) with realistic correlated distributions
- [ ] Write a simple evaluation check for the matching engine: pick ~10 seeded profiles, manually decide their "expected" top-3 matches, run the engine, and report how many match. Label this explicitly as a **synthetic sanity check against our own assumptions**, not a real-world accuracy claim — never report this as a validated accuracy percentage
- [ ] Write an equivalent evaluation statement for the Readiness Score and Placement Support flags — a **face-validity review**: manually inspect ~10 seeded student profiles, confirm the readiness band and any support-priority flag each receives matches what a human would reasonably expect given their inputs, and note any mismatches. This satisfies the official deliverable "accuracy/performance evaluation of matching and scoring" for the scoring side, not just matching — per `ARCHITECTURE.md` §9, do not report a fabricated accuracy percentage here either

**Definition of done:** The full lifecycle — Profiling → Matching → Scheduling → Notification → Offer Tracking → Analytics — works end-to-end on the live deployment, and both evaluation statements (Matching Engine sanity check + Readiness/Support-flag face-validity review) are written down, not just implied.

---

## Phase 5 — Polish, Docs & Demo Rehearsal (Final Day)

- [ ] UI pass: consistent branding (navy/saffron/green), Hinglish voice per `DESIGN.md`
- [ ] Lock CORS to the real Vercel origin (remove `allow_origins=["*"]`)
- [ ] Confirm system architecture diagram and algorithm documentation are ready to present
- [ ] Rehearse the live demo flow in order: Profiling → Matching → Scheduling → Offer → Analytics
- [ ] Read `JUDGE_REVIEW.md` yourself, out loud, once — internalize the honest answers to hard questions before the demo
- [ ] Write a one-paragraph **Scalability & Deployment Approach** statement (add to `ARCHITECTURE.md` §9 or a new README section) describing the multi-campus design explicitly: every core table carries a `college_id` column enforced by both application-level filtering and a PostgreSQL Row-Level Security policy, so one deployment can serve multiple colleges as isolated tenants without re-architecture. This is an official minimum deliverable ("scalability and deployment approach across multiple campuses") — it must exist as a written statement, not just as implemented code
- [ ] Open the live app ~5 minutes before the demo slot (Render free tier cold-start warm-up)
- [ ] Update `MEMORY.md` with final state and known limitations

---

## 🟢 Stretch Goals (P2 — only after everything above is solid)

- [ ] Jugaad Simulator ("what if we train 200 students in AWS?") — reposition as an application of an established workforce-planning technique to an underserved category (see `RESEARCH_AUDIT.md` Phase 9), not an invention
- [ ] Semantic matching via sentence-transformers + pgvector — only after the rule-based Matching Engine works end-to-end
- [ ] Gamified preparation tracker
- [ ] PWA / mobile-friendly layout

**Explicitly removed from scope (see `TECHNICAL_VALIDATION.md` Phase 10):**
- ~~AI Mock Interview~~ — dropped entirely. 10+ mature dedicated competitors exist; a hackathon version cannot compete and adds no differentiation.
- ~~AI Career Chatbot~~ — "Jugaad Dost" ships only as a static UI label / FAQ panel, never as a built LLM-backed chatbot.

**Rule:** Do not start any stretch goal until every Phase 0–5 box above is checked and deployed.

---

## ✅ Official Minimum Deliverables — Full Coverage Check

Cross-referenced against the CampusLink problem statement's 12 minimum deliverables. All 12 are now covered by the phases above:

| # | Deliverable | Covered In |
|---|---|---|
| 1 | Working prototype (deployed) | Phase 0 |
| 2 | Student readiness/employability scoring | Phase 1 |
| 3 | Matching for ≥3 simulated drives | Phase 2 |
| 4 | Conflict-aware drive scheduling | Phase 3 |
| 5 | Explainable shortlisting/matching output | Phase 2 |
| 6 | Placement monitoring dashboard | Phase 3 |
| 7 | Offer and documentation tracking | Phase 4 |
| 8 | System architecture | `ARCHITECTURE.md` + Technical Documentation |
| 9 | Details of models/algorithms used | `ARCHITECTURE.md` §5, `TECHNICAL_VALIDATION.md` |
| 10 | Demonstration using simulated/public datasets | Synthetic dataset + `Placement_Data_Full_Class.csv` |
| 11 | Accuracy/performance evaluation of matching **and scoring** | Phase 4 (both evaluation bullets) |
| 12 | Scalability/deployment approach across multiple campuses | Phase 5 (written statement) |
