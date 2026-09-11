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
                        │  + pgvector (P2)     │
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
| Resume parsing | pdfplumber / PyMuPDF |
| ML (P1/P2) | scikit-learn, sentence-transformers |

### Database
| Layer | Technology |
|---|---|
| Primary DB | PostgreSQL |
| Vector search (P2) | pgvector |

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

### Match AI
```
Student Profile + Job Requirements → Eligibility Rules (hard filters:
CGPA, branch) → Skill Matching (keyword/weighted) → [P2: Embedding
Similarity via pgvector] → Weighted Ranking → Explanation Generator
```
Output always includes: total score, per-factor contribution, and the specific missing requirement(s) in the required explanation format.

### Scheduling Engine
```
New Interview Request → Check Student Availability → Check Venue →
Check Panel → Check Overlapping Drives → Conflict? → Propose Next
Free Slot : Confirm
```
Implemented as **deterministic rule-based conflict checking**, not an LLM call — scheduling must be reliable and repeatable.

### Predictive AI (At-Risk)
```
Historical/Synthetic Data → Feature Engineering (skill gaps, mock
interview score, drive participation, application activity) →
scikit-learn classifier (or rule-based threshold for MVP) →
Risk Level + Contributing Factors → Recommendation
```

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
- CORS locked to the known frontend origin in production.
- No secrets committed to the repo — all via environment variables (see `RULES.md`).
