import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from backend.database import SessionLocal
from backend import models
from backend.engines import scheduling

fake = Faker()
COLLEGE_ID = str(uuid.uuid4())

def generate_student(college_id: str, is_at_risk=False):
    password = "password123"
    user = models.User(
        email=fake.unique.email(),
        password_hash="",
        role="student",
        college_id=college_id,
    )
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.password_hash = pwd_ctx.hash(password)
    
    # If at_risk, deliberately assign bad scores and backlogs
    student = models.Student(
        name=fake.name(),
        branch=random.choice(["CSE", "ECE", "ME", "CE"]),
        cgpa=round(random.uniform(5.0, 9.5)) if not is_at_risk else round(random.uniform(3.0, 5.0), 2),
        backlog_count=random.randint(0, 2) if not is_at_risk else random.randint(3, 5),
        technical_score=round(random.uniform(50, 100), 2) if not is_at_risk else random.uniform(20, 40),
        project_score=round(random.uniform(50, 100), 2) if not is_at_risk else random.uniform(20, 40),
        aptitude_score=round(random.uniform(50, 100), 2) if not is_at_risk else random.uniform(20, 40),
        communication_score=round(random.uniform(50, 100), 2) if not is_at_risk else random.uniform(20, 40),
        interview_score=round(random.uniform(50, 100), 2) if not is_at_risk else random.uniform(20, 40),
        readiness_score=round(random.uniform(60, 100), 2) if not is_at_risk else random.uniform(20, 40),
        college_id=college_id,
        created_at=datetime.utcnow(),
    )
    
    skills = []
    if not is_at_risk:
        skills = [
            models.StudentSkill(
                skill_name=skill,
                proficiency=random.randint(60, 100),
                college_id=college_id,
            ) for skill in random.sample(["Python", "Java", "C++", "SQL", "React", "Node.js", "Excel", "JavaScript"], k=random.randint(2, 5))
        ]
    # At-risk student gets NO skills to trigger the skill gap rule
    
    return user, student, skills

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

def seed_phase3(student_count=300, company_count=12):
    db = SessionLocal()
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    try:
        # Create an admin user
        admin_user = models.User(
            email="admin@example.com",
            password_hash=pwd_ctx.hash("admin123"),
            role="admin",
            college_id=COLLEGE_ID,
        )
        db.add(admin_user)
        
        # Create a single recruiter user for each company
        jobs = []
        for _ in range(company_count):
            recruiter_user = models.User(
                email=fake.unique.email(),
                password_hash=pwd_ctx.hash("password123"),
                role="recruiter",
                college_id=COLLEGE_ID,
            )
            db.add(recruiter_user)
            db.flush()
            
            company = generate_company(recruiter_user.id, COLLEGE_ID)
            db.add(company)
            db.flush()
            
            for _ in range(random.randint(2, 3)):
                job = generate_job(company.id, COLLEGE_ID)
                db.add(job)
                jobs.append(job)
                
        # Generate students (normal)
        all_students = []
        for _ in range(student_count - 5):
            user, student, skills = generate_student(COLLEGE_ID, is_at_risk=False)
            db.add(user)
            db.flush()
            student.user_id = user.id
            db.add(student)
            db.flush()
            for skill in skills:
                skill.student_id = student.id
                db.add(skill)
            all_students.append(student)
            
        # Generate at-risk students
        for _ in range(5):
            user, student, skills = generate_student(COLLEGE_ID, is_at_risk=True)
            db.add(user)
            db.flush()
            student.user_id = user.id
            db.add(student)
            db.flush()
            all_students.append(student)

        db.flush()

        # Deliberate Double Booking Scenario
        if len(jobs) >= 2 and len(all_students) >= 1:
            job1 = jobs[0]
            job2 = jobs[1]
            student = all_students[0]
            
            # Recruiter 1 tries to schedule an interview at tomorrow 10:00 AM
            preferred_start = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            start_time_1, end_time_1 = scheduling.propose_schedule(
                job_id=str(job1.id),
                student_id=str(student.id),
                preferred_start=preferred_start,
                duration_minutes=30,
                venue="Room 101",
                panel="Panel A",
                db=db
            )
            interview1 = models.Interview(
                job_id=job1.id,
                student_id=student.id,
                start_time=start_time_1,
                end_time=end_time_1,
                venue="Room 101",
                panel="Panel A",
                college_id=COLLEGE_ID
            )
            db.add(interview1)
            db.flush()
            
            # Recruiter 2 tries to schedule an interview at EXACTLY the same time (tomorrow 10:00 AM)
            # The engine should push it forward!
            start_time_2, end_time_2 = scheduling.propose_schedule(
                job_id=str(job2.id),
                student_id=str(student.id),
                preferred_start=preferred_start,
                duration_minutes=30,
                venue="Room 102",
                panel="Panel B",
                db=db
            )
            interview2 = models.Interview(
                job_id=job2.id,
                student_id=student.id,
                start_time=start_time_2,
                end_time=end_time_2,
                venue="Room 102",
                panel="Panel B",
                college_id=COLLEGE_ID
            )
            db.add(interview2)
            db.flush()
            print(f"Double booking resolved! Preferred: {preferred_start}, Int1: {start_time_1}, Int2: {start_time_2}")

        db.commit()
        print(f"✅ Seeded {student_count} students (including 5 at-risk), {company_count} companies, 1 admin")
    finally:
        db.close()

if __name__ == "__main__":
    seed_phase3()
