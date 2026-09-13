# JobJugaad — Product Requirements Document (PRD)

**Tagline:** Placement ka Jugaad, AI ke Saath.
**Event:** BPUT Hackathon 2026 — Problem Statement 10 (CampusLink)
**Status:** Draft v1.0

---

## 1. Overview

JobJugaad is an **explainability-first** campus-to-corporate placement intelligence platform. It replaces the spreadsheets, WhatsApp groups, and manual shortlisting that placement cells currently rely on with a single system that covers the full placement lifecycle:

```
Profile → Readiness → Skill Gap → Opportunity → Matching → Shortlisting →
Scheduling → Interview → Offer → Documentation → Joining → Analytics
```

**Core positioning (revised per `REVISED_DOCUMENTATION.md` Phase 17):** JobJugaad connects student readiness, opportunity matching, conflict-aware scheduling, predictive intervention, offer tracking, and placement analytics into one workflow — using deterministic, auditable logic wherever it suffices, and machine learning only where free-text parsing or class-imbalanced prediction genuinely requires it. It doesn't just tell colleges what happened — it tells them who needs help, who fits which opportunity, where the process is breaking, and what intervention could improve outcomes.

> **Honest competitive framing (see `RESEARCH_AUDIT.md`):** this is not the first AI-powered campus placement platform — at least 8 commercial products (Superset, PlacementPilot AI, Relatezone, CNEAR Falcon, LeetCampus, iamneo, Naukri RMS) and one very close open-source analogue (SkillBridge) already exist. Resume parsing, basic matching, scheduling, and analytics are table stakes across this category — never pitch them as innovative. The three defensible differentiators, confirmed absent from every reviewed competitor, are: **(1)** consistent factor-level explainable matching in the official "Below Threshold: ..." format, **(2)** placement-specific at-risk prediction, and **(3)** the Jugaad Simulator's what-if intervention modeling. Lead with these three, not with "AI-powered" generally.

---

## 2. Problem Statement

| Stakeholder | Pain Points |
|---|---|
| **Students** | Don't know their readiness level, which skills are missing, which jobs they qualify for, why they were rejected, or what to learn next. |
| **Recruiters** | Face large candidate pools, manual resume screening, inconsistent comparison, scheduling complexity, no explainability in ranking. |
| **Placement Cells** | Spreadsheet-heavy workflows, multiple simultaneous drives, scheduling conflicts, manual offer/documentation tracking, no visibility into at-risk students or conversion trends. |

---

## 3. Goals & Success Metrics

| Goal | Metric |
|---|---|
| Give students actionable readiness feedback | Every student has a Readiness Score + at least 1 skill-gap recommendation |
| Give recruiters trustworthy, ranked shortlists | Every match has an explainable score breakdown, not just a raw percentage |
| Eliminate scheduling conflicts | 100% of double-booked interview slots are auto-detected before confirmation |
| Give placement cells predictive visibility | At-risk students are flagged before they become unplaced |
| Ship a working, deployed prototype | Live URL demoable end-to-end across all 3 portals by hackathon deadline |

---

## 4. Target Users

### 4.1 Students (Career Copilot)
- Build professional profile, upload resume
- View readiness score and skill gaps
- Discover ranked job opportunities
- Track applications, interviews, and offers
- Receive notifications

### 4.2 Recruiters (Talent Finder)
- Create company profile and placement drives
- Define job requirements and eligibility criteria
- Run AI matching against the candidate pool
- Understand match reasoning (explainability)
- Schedule interviews, manage offers

### 4.3 Placement Administrators (Placement Command Center)
- Manage students, recruiters, and drives
- Resolve scheduling conflicts
- Track offers and documentation
- Identify at-risk students
- Analyze placement trends, run "what-if" simulations

---

## 5. Feature Requirements (Prioritized)

### 🔴 P0 — Must Work (hackathon survival layer)

| Area | Features |
|---|---|
| Student | Profile, resume parsing, readiness score, skill-gap analysis |
| Recruiter | Company profile, JD/drive creation, requirement extraction, eligibility filtering, AI matching, explainable ranking |
| Admin | Drive management, conflict detection, scheduling, placement analytics, at-risk prediction, offer tracking |

### 🟡 P1 — Should Work

- Notifications (simulated)
- Interview tracking
- Documentation tracking
- Joining status
- Recruiter analytics, package analytics, skill conversion analytics

### 🟢 P2 — Optional / Future

- Jugaad Simulator ("what if we train 200 students in AWS?") — genuine differentiator, build only after P0/P1 are solid
- Semantic matching via embeddings (sentence-transformers + pgvector) — real differentiator per research, but adds infra complexity; attempt only after the rule-based Matching Engine works end-to-end
- Gamified preparation
- PWA / mobile experience

> **Dropped per `TECHNICAL_VALIDATION.md` Phase 10:** **AI Mock Interview** is removed from the roadmap entirely — 10+ mature dedicated competitors exist (Eklavvya, Interview Pilot, Final Round AI, Google Interview Warm-Up), and a hackathon-quality version cannot compete. **AI Career Chatbot ("Jugaad Dost")** is demoted to a static UI label / FAQ panel, not a built LLM feature — an academic prototype (Campus-Connect) already ships a near-identical GPT-based chatbot, so building one adds no differentiation for real effort.

---

## 6. Key User Stories

**Student**
- As a student, I want to upload my resume and get a readiness score, so I know how employable I currently am.
- As a student, I want to see exactly which skills I'm missing for a target role, so I know what to learn next.
- As a student, I want to see why I wasn't shortlisted, so I can improve instead of guessing.

**Recruiter**
- As a recruiter, I want to post a job and get a ranked candidate list instantly, so I don't manually screen hundreds of resumes.
- As a recruiter, I want to see *why* a candidate ranked where they did, so I can trust the shortlist.

**Admin**
- As a placement officer, I want the system to flag scheduling conflicts automatically, so I don't double-book a student.
- As a placement officer, I want to see which students are at risk of remaining unplaced, so I can intervene early.
- As a placement officer, I want branch/skill/package analytics, so I can report outcomes to college leadership.

---

## 7. Explainability Requirement (Critical)

Per the official problem statement, every rejection/ranking must be explainable in this style:

> "Below Threshold: The student's CGPA meets the eligibility criteria, but the required skill set shows a gap in cloud technologies and the mock-interview score is below the recruiter's expected benchmark."

Readiness/fit level should also map to the official four-band scale:
**Not Ready → Developing → Ready → Highly Employable**

---

## 8. Non-Functional Requirements

- **Explainability:** No black-box scores — every score must show its contributing factors.
- **Multi-tenancy:** Data model must support multiple colleges (`college_id` on core tables).
- **Availability:** Deployed and demoable, not localhost-only.
- **Performance:** Matching against a few thousand synthetic student rows should return in a few seconds.
- **Security:** Role-based access control (student/recruiter/admin) enforced on every endpoint via JWT.

---

## 9. Out of Scope (for hackathon MVP)

- Real production WhatsApp/SMS integration (simulated notifications only)
- Blockchain-based offer verification
- LinkedIn/job-portal API integrations
- Multi-language support
- Production-grade Alembic migrations (raw `create_all` is acceptable for MVP)

---

## 10. Assumptions & Constraints

- No real student/recruiter data is available — a synthetic dataset (~4,800 students, 40–50 companies) will be generated.
- Team has React/JS experience; Python/FastAPI is the backend learning curve.
- Deployment target: **Vercel** (frontend) + **Render** (backend + PostgreSQL).
- Timeline: hackathon-length (days, not months) — see `PHASES.md`.

---

## 11. Related Documents

- `ARCHITECTURE.md` — system design, stack, schema, API
- `RULES.md` — coding conventions and workflow rules
- `PHASES.md` — build roadmap and day-by-day plan
- `DESIGN.md` — brand, UI/UX, and voice guidelines
- `MEMORY.md` — living project state and decision log
- `RESEARCH_AUDIT.md` — competitive research; what's common vs. genuinely differentiated
- `TECHNICAL_VALIDATION.md` — research-backed validation of the AI/ML, matching, and scheduling design
- `REVISED_DOCUMENTATION.md` — the full before/after refinement log behind this document's changes
- `JUDGE_REVIEW.md` — hard questions judges will ask, answered honestly — read before your demo
