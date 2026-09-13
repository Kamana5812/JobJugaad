import random
import uuid
from datetime import datetime
from faker import Faker
from backend.database import SessionLocal
from backend import models

fake = Faker()

# Utility to generate a random college UUID for multi‑tenant testing
COLLEGE_ID = str(uuid.uuid4())

def generate_student(college_id: str):
    # Reuse existing generate_student logic from seed.py but ensure college_id passed
    password = "password123"
    user = models.User(
        email=fake.unique.email(),
        password_hash="",  # will be replaced after hashing
        role="student",
        college_id=college_id,
    )
    # Hash password
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.password_hash = pwd_ctx.hash(password)
    # Create associated student record
    student = models.Student(
        name=fake.name(),
        branch=random.choice(["CSE", "ECE", "ME", "CE"]),
        cgpa=round(random.uniform(5.0, 9.5), 2),
        backlog_count=random.randint(0, 2),
        technical_score=round(random.uniform(50, 100), 2),
        project_score=round(random.uniform(50, 100), 2),
        aptitude_score=round(random.uniform(50, 100), 2),
        communication_score=round(random.uniform(50, 100), 2),
        interview_score=round(random.uniform(50, 100), 2),
        college_id=college_id,
        created_at=datetime.utcnow(),
    )
    return user, student, [
        models.StudentSkill(
            skill_name=skill,
            proficiency=random.randint(30, 100),
            college_id=college_id,
        ) for skill in random.sample(["Python", "Java", "C++", "SQL", "React", "Node.js", "Excel", "JavaScript"], k=random.randint(2, 5))
    ]

def generate_company(recruiter_user_id: str, college_id: str):
    company = models.Company(
        recruiter_user_id=recruiter_user_id,
        name=fake.company(),
        industry=fake.bs(),
        college_id=college_id,
        created_at=datetime.utcnow(),
    )
    return company

def generate_job(company_id: str, college_id: str):
    # Random required skills map
    possible_skills = ["Python", "Java", "C++", "SQL", "React", "Node.js"]
    required_skills = {skill: random.randint(60, 100) for skill in random.sample(possible_skills, k=3)}
    job = models.Job(
        company_id=company_id,
        title=fake.job(),
        ctc=round(random.uniform(5, 15), 2),
        min_cgpa=round(random.uniform(6.0, 8.0), 2),
        eligible_branches=random.sample(["CSE", "ECE", "ME", "CE"], k=2),
        required_skills=required_skills,
        college_id=college_id,
        created_at=datetime.utcnow(),
    )
    return job

def seed_phase2(student_count=300, company_count=12):
    db = SessionLocal()
    try:
        # Create a single recruiter user for each company
        for _ in range(company_count):
            # Recruiter user
            recruiter_user = models.User(
                email=fake.unique.email(),
                password_hash="",
                role="recruiter",
                college_id=COLLEGE_ID,
            )
            from passlib.context import CryptContext
            pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
            recruiter_user.password_hash = pwd_ctx.hash("password123")
            db.add(recruiter_user)
            db.flush()  # get recruiter_user.id
            # Company
            company = generate_company(recruiter_user.id, COLLEGE_ID)
            db.add(company)
            db.flush()
            # Create 2‑3 drives per company
            for _ in range(random.randint(2, 3)):
                job = generate_job(company.id, COLLEGE_ID)
                db.add(job)
        # Generate students
        for _ in range(student_count):
            user, student, skills = generate_student(COLLEGE_ID)
            db.add(user)
            db.flush()
            student.user_id = user.id
            db.add(student)
            db.flush()
            for skill in skills:
                skill.student_id = student.id
                db.add(skill)
        db.commit()
        print(f"✅ Seeded {student_count} students, {company_count} companies with drives")
    finally:
        db.close()

if __name__ == "__main__":
    seed_phase2()
