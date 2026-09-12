import database, models, auth
import random
from datetime import datetime

def run_seed():
    db = database.SessionLocal()
    
    # Check if already seeded with new volume
    if db.query(models.Student).count() >= 300:
        print("Database already seeded with enough students")
        return
        
    print("Seeding database (Scale Up Phase 2)...")
    
    branches = ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"]
    skills_pool = ["Python", "Java", "JavaScript", "React", "SQL", "AWS", "Machine Learning", "C++", "Docker", "Node.js"]
    
    # Create up to 300 students
    existing_count = db.query(models.Student).count()
    for i in range(existing_count + 1, 301):
        email = f"student{i}@example.com"
        pwd = auth.get_password_hash("password123")
        
        user = models.User(email=email, password_hash=pwd, role="student", college_id="bput_college_1")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        student = models.Student(
            user_id=user.id,
            name=f"Student {i}",
            branch=random.choice(branches),
            cgpa=round(random.uniform(5.5, 9.8), 2),
            aptitude_score=round(random.uniform(40, 95), 1),
            communication_score=round(random.uniform(40, 95), 1),
            interview_score=round(random.uniform(40, 95), 1),
            college_id="bput_college_1"
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        
        num_skills = random.randint(2, 6)
        selected_skills = random.sample(skills_pool, num_skills)
        for skill in selected_skills:
            student_skill = models.StudentSkill(student_id=student.id, skill_name=skill, proficiency=random.randint(40, 95))
            db.add(student_skill)
            
    print("Students seeded.")
    
    # Create 10 Companies
    industries = ["Software", "Fintech", "Consulting", "EdTech"]
    company_objs = []
    
    for i in range(1, 11):
        email = f"recruiter{i}@company.com"
        # Avoid duplicate recruiters if script re-runs
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            continue
            
        pwd = auth.get_password_hash("password123")
        user = models.User(email=email, password_hash=pwd, role="recruiter", college_id="bput_college_1")
        db.add(user)
        db.commit()
        db.refresh(user)
        
        company = models.Company(
            recruiter_user_id=user.id,
            name=f"Company {i} Tech",
            industry=random.choice(industries)
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        company_objs.append(company)

    print("Companies seeded.")

    if not company_objs:
        company_objs = db.query(models.Company).limit(10).all()

    # Create 3 Simulated Drives
    if db.query(models.Job).count() < 3 and company_objs:
        drives = [
            {"title": "SDE Intern", "ctc": 12.0, "min_cgpa": 7.5, "branches": ["Computer Science", "Information Technology"], "skills": ["Java", "SQL"]},
            {"title": "Frontend Developer", "ctc": 8.5, "min_cgpa": 6.5, "branches": ["Computer Science", "Information Technology", "Electronics"], "skills": ["JavaScript", "React"]},
            {"title": "Cloud Engineer", "ctc": 15.0, "min_cgpa": 8.0, "branches": ["Computer Science"], "skills": ["AWS", "Docker", "Python"]},
        ]
        
        for d in drives:
            job = models.Job(
                company_id=random.choice(company_objs).id,
                title=d["title"],
                ctc=d["ctc"],
                min_cgpa=d["min_cgpa"],
                eligible_branches=d["branches"],
                required_skills=d["skills"],
                college_id="bput_college_1"
            )
            db.add(job)
            
        db.commit()
        print("Drives seeded.")

    db.close()
    print("Phase 2 Seed Complete.")

if __name__ == "__main__":
    database.Base.metadata.create_all(bind=database.engine)
    run_seed()
