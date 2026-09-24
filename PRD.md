# JobJugaad — Product Requirements Document (PRD)

**Tagline:** Placement ka Jugaad, AI ke Saath.
**Event:** BPUT Hackathon 2026 — Problem Statement 10 (CampusLink)
**Status:** Phase 5 implementation-aligned requirements; aspirational items are labeled below.

---

## 1. Overview

JobJugaad is an **explainability-first** campus-to-corporate placement intelligence platform. It replaces the spreadsheets, WhatsApp groups, and manual shortlisting that placement cells currently rely on with a single system that covers the full placement lifecycle:

```
Profile → Readiness → Skill Gap → Opportunity → Matching → Shortlisting →
Scheduling → Interview → Offer → Documentation → Joining → Analytics
```

**Core positioning:** JobJugaad connects readiness, keyword/weighted matching, conflict-aware scheduling, rule-based support, offers and analytics. The deployed workflow uses deterministic calculations and fixed explanations with human review. A separately authorized public-data Random Forest placement-status model is integrated alongside weighted readiness after metric review. It uses optional compatible academic records and supplies a score, local factors and explanation; it never changes recruitment decisions. No LLM is used.

> **Honest competitive framing:** Campus placement platforms already exist; no first-mover or exclusive-feature claim is made. Demonstrate visible factor-level evidence, named support indicators, human overrides and the connected workflow. The simulator is future work. Historical research files are absent from this checkout; their competitor counts and uniqueness assertions are not evidence for the final pitch.

**Core product philosophy: Reject Less → Identify the Gap → Help the Student Improve.** When a student doesn't match a role, the system's job does not end at "Not Eligible." It identifies the specific skill, communication, or aptitude gap and turns it into an actionable next step. This principle governs the Readiness Engine, the Matching Engine, and the Placement Support system consistently — see Section 7 and Section 11.

---

## 2. Problem Statement

| Stakeholder | Pain Points |
|---|---|
| **Students** | Don't know their readiness level, which skills are missing, which jobs they qualify for, why they were rejected, or what to learn next. |
| **Recruiters** | Face large candidate pools, manual resume screening, inconsistent comparison, scheduling complexity, no explainability in ranking. |
| **Placement Cells** | Spreadsheet-heavy workflows, multiple simultaneous drives, scheduling conflicts, manual offer/documentation tracking, no visibility into which students may need additional support or how conversion trends are shifting. |

---

## 3. Goals & Success Metrics

These are product targets, not measured benchmarks.

| Goal | Metric |
|---|---|
| Give students actionable readiness feedback | Every student has a Readiness Score + at least 1 skill-gap recommendation |
| Give recruiters trustworthy, ranked shortlists | Every match has an explainable score breakdown, not just a raw percentage |
| Eliminate scheduling conflicts | Check recorded student, venue and panel overlaps before confirmation; no universal detection-rate claim |
| Give placement cells support visibility | Students who may need additional placement support are flagged early, based on measurable indicators, before they go unplaced |
| Ship a working, deployed prototype | Live URL demoable end-to-end across all 3 portals by hackathon deadline |

---

**Current boundary:** Students have profile/readiness, offers and notifications. Recruiters manage company/drives/matching; admins manage scheduling/offers/support/analytics. Student opportunities/applications, recruiter scheduling, automatic JD extraction and simulator remain roadmap items. A public-data MBA placement signal is deployed; the user also authorized a separate BTech / BE signal using compatible engineering records. Both remain distinct from weighted readiness.

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
- Run keyword/weighted matching against the candidate pool
- Understand match reasoning (explainability)
- Schedule interviews, manage offers

### 4.3 Placement Administrators (Placement Command Center)
- Manage students, recruiters, and drives
- Resolve scheduling conflicts (with final approval before confirmation)
- Track offers and documentation
- Identify students who may need additional placement support
- Analyze placement trends, run "what-if" simulations
- Review, override, or dismiss any calculated recommendation

---

## 5. Feature Requirements (Prioritized)

### 🔴 P0 — Must Work (hackathon survival layer)

| Area | Features |
|---|---|
| Student | Profile, resume parsing, readiness score, skill-gap analysis |
| Recruiter | Company profile, structured drive creation, manually entered requirements, eligibility filtering, keyword/weighted matching, explainable ranking |
| Admin | Drive management, conflict detection (admin-approved), scheduling, placement analytics, rule-based placement-support indicators, offer tracking |

### 🟡 P1 — Should Work

- Notifications (simulated)
- Interview tracking
- Documentation tracking
- Joining status
- Recruiter analytics, package analytics, skill conversion analytics

### 🟢 P2 — Optional / Future

- Jugaad Simulator ("what if we train 200 students in AWS?") — future capability requiring explicit authorization
- Semantic matching via embeddings (sentence-transformers + pgvector) — future capability requiring explicit authorization
- Gamified preparation
- PWA / mobile experience

> **Excluded by user scope:** AI Mock Interview is not built. Jugaad Dost is a static FAQ/help label only; no live chatbot.

---

## 6. Key User Stories

**Student**
- As a student, I want to upload my resume and get a readiness score, so I know how employable I currently am.
- As a student, I want to see exactly which skills I'm missing for a target role, so I know what to learn next.
- As a student, I want to see why I wasn't shortlisted, so I can improve instead of guessing.

**Recruiter**
- As a recruiter, I want to post a job and get a ranked candidate list, so I don't manually screen hundreds of resumes.
- As a recruiter, I want to see *why* a candidate ranked where they did, so I can trust the shortlist.

**Admin**
- As a placement officer, I want the system to flag scheduling conflicts automatically, so I don't double-book a student — with the final schedule always subject to my approval.
- As a placement officer, I want to see which students may need additional placement support and why, so I can intervene early rather than after the fact.
- As a placement officer, I want branch/skill/package analytics, so I can report outcomes to college leadership.

---

## 7. Explainability Requirement (Critical)

Per the official problem statement, every rejection/ranking must be explainable in this style:

> "Below Threshold: The student's CGPA meets the eligibility criteria, but the required skill set shows a gap in cloud technologies and the mock-interview score is below the recruiter's expected benchmark."

Readiness/fit level should also map to the official four-band scale:
**Not Ready → Developing → Ready → Highly Employable**

**Responsible language requirement:** the system never claims to "understand" a student — output is described as a rule-based, structured view of their current profile. Support-priority flags never imply a student will fail or is unsuccessful; they identify measurable indicators and route them to a human for review. A rejection is never a dead end — it always carries the specific gap behind it and, where possible, a suggested next step (see Section 1's "Reject Less" philosophy).

---

## 8. Non-Functional Requirements

- **Explainability:** No black-box scores — every score must show its contributing factors.
- **Multi-tenancy:** Data model must support multiple colleges (`college_id` on core tables).
- **Availability:** Deployed and demoable, not localhost-only.
- **Performance target, not a measured claim:** evaluate matching latency on representative deployment resources before promising response times.
- **Security:** Role-based access control (student/recruiter/admin) enforced on every endpoint via JWT, backed by database-level Row-Level Security. No absolute claims ("100% secure," "military-grade") are made anywhere in product materials.
- **Human oversight:** Every calculated ranking, schedule change, or support flag must be reviewable, editable, or dismissible by a placement administrator or recruiter — the system provides decision support, never an autonomous final decision-maker.

---

## 9. Out of Scope (for hackathon MVP)

- Real production WhatsApp/SMS integration (simulated notifications only)
- Blockchain-based offer verification
- LinkedIn/job-portal API integrations
- Multi-language support
- Production-grade Alembic migrations (raw `create_all` is acceptable for MVP)
- Long-term post-joining career outcome tracking (beyond the joining/offer stage) — not claimed unless actually implemented in the prototype

---

## 10. Assumptions & Constraints

- Hybrid data: imported public Campus Recruitment placement labels (215 records) are reserved for a separate academic/work-experience placement classifier. The 4,800 student / 45 company application demo, skills, projects, certifications and workflow records remain synthetic. The source has no resume/skills/project evidence; its labels do not validate matching or readiness rules.
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

## Authorized hybrid-data experiment — 2026-09-24

Accuracy **88.37%**, precision **93.10%**, recall **90.00%**, F1 **91.53%** (positive class: Placed; **43 held-out records**, 172 training, 215 total). This separate Random Forest uses the imported public Campus Recruitment status labels; it is not validation of weighted readiness, matching or support rules. Only the dataset's academic/test/work-experience and categorical fields are modeled; source collection is publisher-reported and the small MBA-oriented sample is not a BPUT outcome benchmark. [Measured report](backend/ml/EVALUATION.md). The user authorized integration after reviewing these metrics. The public dataset need not come from BPUT. Missing compatible academic fields produce no model score.

**BTech extension:** separate optional four-field public-data Random Forest (semester-6 CGPA, engineering stream, internships, ever-backlog history), no MBA requirement. Six represented engineering streams only, with full local model contributions and explanations. The public source is publisher-reported 2013–2014 data; grouped held-out evaluation and limits are documented in [the BTech report](backend/ml/engineering/EVALUATION.md). No changes to rule-based matching, readiness, support or offers.
