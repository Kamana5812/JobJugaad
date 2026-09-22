"""Idempotent, deterministic synthetic Phase 1 profiles; no real accuracy data."""
import random
import secrets
from sqlalchemy import select, text
from auth import hash_password
from database import tenant_session, initialize_schema
from models import User, Student
from schemas import ProfileUpdate, SkillInput, EvidenceInput
from engines.profile import save_profile

def seed_students(count=50, college_id=1):
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

if __name__ == "__main__":
    initialize_schema()
    print(f"Created {seed_students()} synthetic student profiles.")
