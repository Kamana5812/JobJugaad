# JobJugaad — Build Phases

Build order for the hackathon. Each phase should end with something deployed and demoable — never work for a full day without pushing to `main`.

---

## Phase 0 — Environment & Skeleton (Day 1)

**Goal:** An empty but fully deployed pipeline, end to end.

- [ ] Install Node.js, Python, Git, VS Code; create GitHub repo `jobjugaad`
- [ ] Create `frontend/` (Vite + React + Tailwind) and `backend/` (FastAPI) folders
- [ ] Backend: minimal `main.py` with a `/health` endpoint
- [ ] Frontend: minimal landing page hitting `/health` and displaying the result
- [ ] Push to GitHub
- [ ] Deploy backend to Render (Web Service, free tier)
- [ ] Create Render Managed PostgreSQL instance, connect `DATABASE_URL`
- [ ] Deploy frontend to Vercel, set `VITE_API_URL` to the live Render URL
- [ ] Confirm: opening the Vercel URL shows a successful call to the live backend

**Definition of done:** A live URL exists and works, even though it does nothing useful yet.

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
- [ ] At-Risk Engine (rule-based or simple scikit-learn classifier): flag students by skill gaps, low mock scores, low activity

**Definition of done:** Admin can see a live dashboard, trigger a scheduling conflict, watch it get resolved, and see at-risk students flagged — all live.

---

## Phase 4 — Offers, Notifications & Data Polish (Day 5)

**Goal:** Complete the lifecycle past "Selected."

- [ ] Database model: `offers` (offer letter, documents, verification, acceptance, joining status)
- [ ] Offer tracking endpoints + frontend views (student and admin sides)
- [ ] Simulated notification engine (in-app notification feed; no real email/SMS needed)
- [ ] Expand and finalize synthetic dataset (~4,800 students, 40–50 companies) with realistic correlated distributions
- [ ] Write a simple accuracy/performance evaluation of the matching engine against labeled test profiles

**Definition of done:** The full lifecycle — Profiling → Matching → Scheduling → Notification → Offer Tracking → Analytics — works end-to-end on the live deployment.

---

## Phase 5 — Polish, Docs & Demo Rehearsal (Final Day)

- [ ] UI pass: consistent branding (navy/saffron/green), Hinglish voice per `DESIGN.md`
- [ ] Lock CORS to the real Vercel origin (remove `allow_origins=["*"]`)
- [ ] Confirm system architecture diagram and algorithm documentation are ready to present
- [ ] Rehearse the live demo flow in order: Profiling → Matching → Scheduling → Offer → Analytics
- [ ] Prepare answers from the mentor/judge Q&A reference doc
- [ ] Open the live app ~5 minutes before the demo slot (Render free tier cold-start warm-up)
- [ ] Update `MEMORY.md` with final state and known limitations

---

## 🟢 Stretch Goals (P2 — only after everything above is solid)

- [ ] Jugaad Simulator ("what if we train 200 students in AWS?")
- [ ] AI Career Chatbot ("Jugaad Dost")
- [ ] AI Mock Interview scoring
- [ ] Semantic matching via sentence-transformers + pgvector
- [ ] Gamified preparation tracker
- [ ] PWA / mobile-friendly layout

**Rule:** Do not start any stretch goal until every Phase 0–5 box above is checked and deployed.
