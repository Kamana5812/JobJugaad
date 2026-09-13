# JobJugaad — Architecture Document

Reference implementation architecture for the JobJugaad platform. See `PRD.md` for requirements and `PHASES.md` for build order.

---

## 1. High-Level System Diagram

```
                        ┌─────────────────────┐
                        │   React Frontend     │
                        │   (Vercel)           │
                        │  /student /recruiter │
                        │  /admin              │
                        └──────────┬───────────┘
                                   │ REST (HTTPS, JSON)
                                   ▼
                        ┌─────────────────────┐
                        │   FastAPI Backend    │
                        │   (Render)           │
                        │  Auth · Routers ·    │
                        │  AI Engines          │
                        └──────────┬───────────┘
                                   │ SQLAlchemy
                                   ▼
                        ┌─────────────────────┐
                        │  PostgreSQL          │
                        │  (Render Managed DB) │
                        │  + Row-Level Security│
                        │  + pgvector (P1/P2,  │
                        │    conditional only) │
                        └─────────────────────┘
```

---

## 2. Tech Stack

### Frontend
| Layer | Technology |
|---|---|
| Framework | React (Vite) |
| Language | JavaScript or TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Routing | React Router |
| HTTP client | Axios |

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Server | Uvicorn |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Auth | JWT (python-jose) + passlib (password hashing) |
| Resume parsing | pdfplumber / PyMuPDF, optionally LLM-assisted for free-text section extraction only (see §5, Profile AI) — this is the one place in the pipeline an LLM is justified |
| ML — **P1, conditional** | scikit-learn (At-Risk classifier only, with class-imbalance handling — see §5) |
| ML — **P2, conditional** | sentence-transformers (semantic matching) — do not install until the P1 rule-based Matching Engine works end-to-end |

### Database
| Layer | Technology |
|---|---|
| Primary DB | PostgreSQL |
| Vector search — **P1/P2, conditional** | pgvector — **not core stack.** Per `TECHNICAL_VALIDATION.md` Phase 16, add this only if semantic matching is actually attempted; installing it for a feature that stays rule-based all hackathon is unnecessary operational complexity |
| Row-level isolation | PostgreSQL Row-Level Security (RLS) policy on every multi-tenant table — see §8 Security |

### Deployment
| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend API | Render (Web Service) |
| Database | Render (Managed PostgreSQL) |

---

## 3. Folder Structure

```
jobjugaad/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── student/        (profile, readiness, skills, opportunities, applications)
│   │   │   ├── recruiter/      (company, drives, candidates, matching, schedule, offers)
│   │   │   └── admin/          (overview, students, drives, at-risk, analytics, simulator)
│   │   ├── components/         (shared UI: cards, tables, charts, pills)
│   │   ├── api/                (axios instance + endpoint wrappers)
│   │   ├── context/             (auth context, role context)
│   │   └── App.jsx
│   ├── .env                    (VITE_API_URL)
│   └── package.json
│
├── backend/
│   ├── main.py                 (app entrypoint, CORS, router registration)
│   ├── database.py             (engine, session, Base)
│   ├── models.py               (SQLAlchemy models — see §4)
│   ├── schemas.py              (Pydantic request/response schemas)
│   ├── auth.py                 (JWT creation/verification, password hashing)
│   ├── engines/
│   │   ├── readiness.py        (Readiness Score calculation)
│   │   ├── skill_gap.py        (Skill Gap Engine)
│   │   ├── matching.py         (Explainable Matching Engine)
│   │   ├── scheduler.py        (Conflict detection)
│   │   ├── risk.py             (At-Risk prediction)
│   │   └── simulator.py        (Jugaad Simulator — P2)
│   ├── routers/
│   │   ├── auth.py
│   │   ├── students.py
│   │   ├── recruiters.py
│   │   └── admin.py
│   ├── seed.py                 (synthetic dataset generator)
│   └── requirements.txt
│
├── PRD.md
├── ARCHITECTURE.md
├── RULES.md
├── PHASES.md
├── DESIGN.md
└── MEMORY.md
```

---

## 4. Database Schema

### Core Entities
```
users, students, recruiters, companies
skills, student_skills, projects, certifications, assessments
jobs, matches
drives, schedules, applications, interviews
offers, documents
notifications
risk_predictions, simulations
```

### Key Tables (fields)

**users**
`id, email, password_hash, role (student|recruiter|admin), college_id, created_at`

**students**
`id, user_id, name, branch, cgpa, backlog_count, resume_text, aptitude_score, communication_score, interview_score, readiness_score, college_id`

**student_skills**
`id, student_id, skill_name, proficiency (0–100)`

**projects / certifications**
`id, student_id, title, description`

**companies**
`id, recruiter_user_id, name, industry`

**jobs (drives)**
`id, company_id, title, ctc, min_cgpa, eligible_branches[], required_skills[], created_at, college_id`

**matches**
`id, job_id, student_id, match_score, factor_breakdown (JSON), missing_requirements (JSON), created_at`

**schedules / interviews**
`id, job_id, student_id, scheduled_time, venue, panel_id, status (upcoming|scheduled|completed|selected|rejected|pending)`

**offers**
`id, student_id, job_id, ctc, offer_letter_status, documents_status, verification_status, acceptance_status, joining_status`

**risk_predictions**
`id, student_id, risk_level (low|medium|high), risk_score, contributing_factors (JSON), recommendation (JSON)`

### Relationships
```
STUDENT ──< Skills
STUDENT ──< Projects
STUDENT ──< Certifications
STUDENT ──< Applications ──> Job
STUDENT ──< Interviews
STUDENT ──< Offers

RECRUITER ──> COMPANY ──< JOBS ──< MATCHES ──> STUDENTS
```

**Multi-tenancy:** every core table carries `college_id` so one deployment can serve multiple colleges; all queries filter by it.

---

## 5. AI / Engine Architecture

### Profile AI
```
Resume → Document Parser (pdfplumber) → Text Extraction →
Keyword/Skill Extraction → Structured Student Profile
```

### Readiness Engine
```
Readiness Score = 30% Technical Skills + 20% Projects + 15% Academics
                + 15% Aptitude + 10% Communication + 10% Interview
```
Maps to official bands: `0–40 Not Ready · 41–65 Developing · 66–85 Ready · 86–100 Highly Employable`

A weighted rule is used deliberately for P0 — not because it's the most accurate option, but because it requires no training data and stays fully auditable, which the explainability requirement demands. **Validated upgrade path (P1):** published research (Kumar et al., 2023, IJMECS) shows Random Forest outperforming comparable weighted/simple-classifier approaches on structured placement data. If upgraded, train against the public **`Placement_Data_Full_Class.csv`** dataset (Ben Roshan's "Campus Recruitment" dataset on Kaggle — confirmed via direct inspection of 5+ independent projects using it) as a real, if small, empirical anchor — not the synthetic demo dataset, which cannot validate real-world accuracy. Note: at least one project using this dataset explicitly warns its small size means reported accuracy "is not guaranteed" — do not overstate confidence even if this upgrade is attempted.

### Match AI
```
Student Profile + Job Requirements → Eligibility Rules (hard filters:
CGPA, branch) → Skill Matching (keyword/weighted) → [P1/P2: Embedding
Similarity via sentence-transformers + pgvector] → Weighted Ranking →
Explanation Generator → Human Override (TPO/recruiter)
```

**Validated methodology (`TECHNICAL_VALIDATION.md` Phase 12):**
- **Normalization:** every component (CGPA, skill overlap %, assessment score, etc.) is scaled to a common 0–100 range before weighting, so no single component silently dominates the sum due to differing units.
- **Weighting:** starting weights (e.g. 32/24/15/12/8/5 across skill compatibility, project relevance, academic eligibility, assessment performance, experience, certifications) are **explicitly unvalidated starting assumptions**, not empirically derived — state this honestly rather than implying they were tuned against real data.
- **Threshold:** a minimum eligible score (e.g. 60/100) below which a candidate is auto-excluded, with the exclusion reason surfaced via the explanation generator.
- **Ranking:** simple descending sort on final score — no additional algorithm needed at hackathon scale.
- **Confidence:** do not report a numeric confidence score at P0 — there is no calibration data to justify one.
- **Explanation:** template-driven (not LLM-generated — see honesty note below), listing top contributing and top missing factors, matching the required "Below Threshold: ..." sentence format exactly.
- **Human override:** the TPO/recruiter must be able to manually promote or reject any candidate regardless of score, with the override logged for auditability.
- **Evaluation:** define, don't fabricate — report precision/recall for the Matching Engine against a small, self-labeled synthetic ground truth (e.g. 10 profiles where you manually decide the "expected" top-3 matches), explicitly caveated as a synthetic sanity check, not a real-world accuracy claim.

Output always includes: total score, per-factor contribution, and the specific missing requirement(s) in the required explanation format.

**Why the explanation generator is template-based, not an LLM call:** the "Below Threshold: ..." format is a fixed template with variable slots — an LLM here would be slower and could hallucinate an incorrect reason, which would be actively harmful to trust. This is the single most important place in the whole pipeline to avoid LLM use.

### Scheduling Engine
```
New Interview Request → Check Student Availability → Check Venue →
Check Panel → Check Overlapping Drives → Conflict? → Propose Next
Free Slot : Confirm
```
Implemented as **deterministic rule-based conflict checking**, not an LLM call — scheduling must be reliable and repeatable. Formally, interview scheduling is a Graph Coloring Problem (NP-complete) per published research (arXiv 2204.08695). At hackathon scale, a greedy constraint-checker is provably sufficient and dramatically lower-risk than a metaheuristic solver (genetic algorithm, ant colony optimization) — do not over-engineer this even though more sophisticated approaches exist in the literature.

### Predictive AI (At-Risk)
```
Historical/Synthetic Data → Feature Engineering (skill gaps, mock
interview score, drive participation, application activity) →
Rule-based thresholds (P0) OR scikit-learn classifier with
class-imbalance handling (P1) → Risk Level + Contributing Factors →
Intervention Recommendation (rule-based lookup, not a prediction task)
```
**Critical methodological requirement if upgraded to a classifier (P1):** at-risk students are always a minority class in any real or synthetic dataset. Per Lee & Chung (2019), a naive classifier trained without addressing this will silently default to predicting "not at risk" for nearly everyone while reporting misleadingly high raw accuracy. Any classifier here **must** use SMOTE oversampling or class weighting — this is not optional, it is the single most commonly cited failure mode in the dropout/at-risk prediction literature reviewed.

### Simulator (P2)
```
Admin Input (e.g. "train 200 students in AWS") → Adjust Synthetic
Skill Distribution → Recompute Eligibility → Apply Historical
Conversion Rate → Projected Eligible Students / Offers
```

---

## 6. API Design (representative endpoints)

```
POST   /auth/signup
POST   /auth/login

GET    /students/{id}/profile
POST   /students/{id}/resume            (upload + parse)
GET    /students/{id}/readiness
GET    /students/{id}/skill-gap?role=Software+Engineer
GET    /students/{id}/opportunities

POST   /recruiters/{id}/companies
POST   /recruiters/{id}/drives
POST   /recruiters/drives/{id}/run-matching
GET    /recruiters/drives/{id}/candidates

POST   /admin/schedule/check-conflict
GET    /admin/analytics/overview
GET    /admin/at-risk
POST   /admin/simulate

GET    /health
```

All authenticated endpoints require a `Bearer <JWT>` header; the token payload includes `user_id`, `role`, and `college_id`.

---

## 7. Deployment Architecture

| Concern | Approach |
|---|---|
| Frontend hosting | Vercel, auto-deploy from `main` branch, root dir `frontend/` |
| Backend hosting | Render Web Service, auto-deploy from `main`, root dir `backend/` |
| Database | Render Managed PostgreSQL (free tier) |
| Env vars (frontend) | `VITE_API_URL` |
| Env vars (backend) | `DATABASE_URL`, `JWT_SECRET` |
| CORS | Backend allows only the deployed Vercel origin in production |
| Cold starts | Render free tier sleeps after 15 min idle — warm up before demos |

---

## 8. Security

- Passwords hashed with `passlib` (bcrypt).
- JWT tokens carry role + college_id; every router checks role before returning data.
- **Two-layer multi-tenancy enforcement:** application-level `WHERE college_id = ...` filtering on every query, **plus** a PostgreSQL Row-Level Security (RLS) policy on every multi-tenant table as a database-enforced second layer. This pattern is confirmed via direct inspection of a comparable real academic platform (`codeecoffee/SmartCampus`), not assumed — it means even an application bug that forgets the filter cannot leak one college's or one student's data into another's results.
- CORS locked to the known frontend origin in production.
- No secrets committed to the repo — all via environment variables (see `RULES.md`).

---

## 9. Dataset & Evaluation

| Category | Status |
|---|---|
| **Real data** | Not used — no real student/recruiter data available or appropriate for a hackathon |
| **Public data** | `Placement_Data_Full_Class.csv` (Ben Roshan's "Campus Recruitment" dataset, Kaggle) — recommended as a real empirical anchor for Readiness Engine weight validation if pursued; confirmed used across 5+ independent public projects |
| **Synthetic data** | ~4,800-student demo dataset (see `seed.py`) — for UI/scale demonstration only, never described as validating model accuracy |
| **Simulated data** | Jugaad Simulator outputs — generated from the synthetic dataset's own conversion model, explicitly labeled as projections, not forecasts |

**Evaluation protocol (do not skip, do not fabricate):**
- Matching Engine: precision/recall against a small, self-labeled synthetic ground truth — label clearly as a sanity check.
- Readiness Engine: face-validity review against manually inspected sample profiles.
- At-Risk classifier (if built past P0 rules): ROC/precision-recall evaluation with class-imbalance-aware methodology (SMOTE or class weighting) — never report raw accuracy alone on an imbalanced classification task.
