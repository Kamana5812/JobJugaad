"""Idempotent synthetic Phase 2 demonstration; not real accuracy data."""
import random
import secrets
from sqlalchemy import select, text
from auth import hash_password
from database import tenant_session, initialize_schema
from models import User, Student
from schemas import ProfileUpdate, SkillInput, EvidenceInput, JobInput
from engines.profile import save_profile

# These are simulated requirements, not statements about real employers.
DEMO_DRIVES = [
    JobInput(title="Simulated Python Backend Engineer", ctc=6, min_cgpa=6, max_backlogs=1,
        eligible_branches=["CSE", "ECE"], required_skills=[dict(skill_name="python", min_proficiency=60), dict(skill_name="sql", min_proficiency=50)]),
    JobInput(title="Simulated React Frontend Engineer", ctc=5.5, min_cgpa=6.5, max_backlogs=0,
        eligible_branches=["CSE", "ECE", "EE"], required_skills=[dict(skill_name="react", min_proficiency=65), dict(skill_name="git", min_proficiency=50)]),
    JobInput(title="Simulated Java Graduate Engineer", ctc=4.5, min_cgpa=5.5, max_backlogs=2,
        eligible_branches=["CSE", "ECE", "ME", "EE"], required_skills=[dict(skill_name="java", min_proficiency=55), dict(skill_name="communication", min_proficiency=50)]),
]

def seed_students(count=300, college_id=1):
    rng = random.Random(2026)
    created = 0
    # Unshared random passwords prevent public login to the synthetic seed accounts.
    unused_hash = hash_password(secrets.token_urlsafe(32))
    with tenant_session(college_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(20260102)"))
        for index in range(1, count + 1):
            email = f"student{index:02d}@demo.jobjugaad.test"
            level = rng.randint(15, 95)
            skills = [SkillInput(skill_name=skill, proficiency=max(0, min(100, level + rng.randint(-15, 15))))
                for skill in rng.sample(["python", "sql", "react", "java", "communication", "git"], 3)]
            projects = [EvidenceInput(title=f"Synthetic project {p + 1}", description="Synthetic coursework example for testing; not a real student achievement.")
                for p in range(rng.randint(0, 5))]
            payload = ProfileUpdate(name=f"Synthetic Student {index:02d}", branch=rng.choice(["CSE", "ECE", "ME", "EE"]),
                cgpa=round(rng.uniform(4, 10), 2), backlog_count=rng.randint(0, 3), skills=skills, projects=projects,
                aptitude_score=level, communication_score=rng.randint(20, 95), interview_score=rng.randint(10, 95),
                certifications=[EvidenceInput(title="Synthetic course completion", description="Demo certificate; not an accredited credential.")] if index % 2 else [])
            if index > 50:
                for project in payload.projects:
                    project.description = "Synthetic coursework using " + ", ".join(s.skill_name for s in skills) + "; demonstration only."
            existing = session.scalar(select(User.id).where(User.email == email, User.college_id == college_id))
            if existing:
                continue
            user = User(email=email, password_hash=unused_hash, college_id=college_id, role="student")
            session.add(user)
            session.flush()
            student = Student(user_id=user.id, college_id=college_id, name=payload.name,
                resume_text=f"Synthetic resume for Student {index:02d}. For testing only.")
            session.add(student)
            session.flush()
            save_profile(session, student, payload)
            created += 1
    return created


def seed_companies(college_id=1):
    from models import Company, Job, Match
    from engines.talent import run_matching
    unused_hash = hash_password(secrets.token_urlsafe(32))
    created = 0
    demonstrations = []
    with tenant_session(college_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(20260103)"))
        for index in range(1, 13):
            email = f"recruiter{index:02d}@demo.jobjugaad.test"
            user = session.scalar(select(User).where(User.email == email, User.college_id == college_id))
            if user is None:
                user = User(email=email, password_hash=unused_hash, role="recruiter", college_id=college_id)
                session.add(user)
                session.flush()
                session.add(Company(college_id=college_id, recruiter_user_id=user.id,
                    name=f"Synthetic Company {index:02d}", industry="Simulated technology services"))
                session.flush()
                created += 1
            company = session.scalar(select(Company).where(Company.college_id == college_id, Company.recruiter_user_id == user.id))
            if index <= len(DEMO_DRIVES):
                payload = DEMO_DRIVES[index - 1]
                job = session.scalar(select(Job).where(Job.college_id == college_id, Job.company_id == company.id, Job.title == payload.title).with_for_update())
                if job is None:
                    job = Job(college_id=college_id, company_id=company.id, **payload.model_dump())
                    session.add(job)
                    session.flush()
                if session.scalar(select(Match.id).where(Match.college_id == college_id, Match.job_id == job.id).limit(1)) is None:
                    demonstrations.append(run_matching(session, job).model_dump())
    return created, demonstrations


if __name__ == "__main__":
    initialize_schema()
    print(f"Created {seed_students()} synthetic students.")
    companies, demonstrations = seed_companies()
    print(f"Created {companies} synthetic companies. New demonstration summaries: {demonstrations}")
