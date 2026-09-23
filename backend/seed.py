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



def seed_phase3(college_id=1):
    from datetime import datetime, timedelta, timezone
    from models import Company, Job, Interview, RiskPrediction
    from engines.scheduling import lock_calendar
    from engines.support import run_support
    created = {"support_students":0, "interviews":0}
    unused_hash = hash_password(secrets.token_urlsafe(32))
    with tenant_session(college_id) as session:
        lock_calendar(session, college_id)
        recruiter = session.scalar(select(User).where(User.college_id == college_id, User.email == "recruiter01@demo.jobjugaad.test"))
        company = session.scalar(select(Company).where(Company.college_id == college_id, Company.recruiter_user_id == recruiter.id))
        job = session.scalar(select(Job).where(Job.college_id == college_id, Job.company_id == company.id, Job.title == "Simulated Cloud Support Track"))
        if job is None:
            payload = JobInput(title="Simulated Cloud Support Track", ctc=5, min_cgpa=5, max_backlogs=3,
                eligible_branches=["CSE","ECE","EE","ME"],
                required_skills=[dict(skill_name=name,min_proficiency=60) for name in ("python","sql","aws","git")])
            job = Job(college_id=college_id, company_id=company.id, **payload.model_dump())
            session.add(job); session.flush()
        support_students = []
        for index in range(1,5):
            email = f"support{index:02d}@demo.jobjugaad.test"
            user = session.scalar(select(User).where(User.college_id == college_id, User.email == email))
            if user is None:
                user = User(college_id=college_id,email=email,password_hash=unused_hash,role="student")
                session.add(user);session.flush()
                student = Student(college_id=college_id,user_id=user.id,name=f"Synthetic Support Student {index:02d}")
                session.add(student);session.flush()
                save_profile(session,student,ProfileUpdate(name=student.name,branch="CSE",cgpa=6.2,
                    skills=[SkillInput(skill_name="python",proficiency=20+index)],projects=[],
                    aptitude_score=35,communication_score=40,interview_score=15+index*5))
                created["support_students"] += 1
            else:
                student = session.scalar(select(Student).where(Student.college_id == college_id,Student.user_id == user.id))
            support_students.append(student)
        now = datetime.now(timezone.utc)
        anchor = (now+timedelta(days=1)).replace(hour=4,minute=30,second=0,microsecond=0)
        student = support_students[0]  # Never attach demonstration bookings to a real account.
        demo_jobs = session.scalars(select(Job).where(Job.college_id == college_id,Job.title.in_([d.title for d in DEMO_DRIVES])).order_by(Job.id).limit(2)).all()
        fixtures = [
            ("phase3-double-booking-a",student.id,demo_jobs[0].id,anchor,"scheduled","demo hall","demo panel"),
            ("phase3-double-booking-b",student.id,demo_jobs[1].id,anchor+timedelta(minutes=15),"scheduled","demo hall","demo panel"),
            ("phase3-participation-a",support_students[3].id,job.id,now-timedelta(days=3),"completed","practice room a","mentor a"),
            ("phase3-participation-b",support_students[3].id,job.id,now-timedelta(days=6),"completed","practice room b","mentor b"),
        ]
        for key, student_id, job_id, start, status, venue, panel in fixtures:
            if session.scalar(select(Interview.id).where(Interview.college_id == college_id,Interview.seed_key == key)) is None:
                # Deliberately imported conflict fixture. Normal API confirmations cannot create conflicts.
                session.add(Interview(college_id=college_id,student_id=student_id,job_id=job_id,scheduled_time=start,
                    end_time=start+timedelta(minutes=30),status=status,venue=venue,panel_id=panel,seed_key=key))
                created["interviews"] += 1
        session.flush()
        if session.scalar(select(RiskPrediction.id).where(RiskPrediction.college_id == college_id,RiskPrediction.job_id == job.id).limit(1)) is None:
            report = run_support(session,recruiter,job.id)
            created["flagged_for_review"] = report.flagged_count
        created["support_job_id"] = job.id
    return created


if __name__ == "__main__":
    initialize_schema()
    print(f"Created {seed_students()} synthetic students.")
    print(seed_companies())
    print(seed_phase3())
