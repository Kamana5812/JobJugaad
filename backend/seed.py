import database, models, auth
import random

def run_seed():
    db = database.SessionLocal()
    
    # Check if already seeded
    if db.query(models.User).count() > 0:
        print("Database already seeded")
        return
        
    print("Seeding database...")
    
    branches = ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"]
    skills = ["Python", "Java", "JavaScript", "React", "SQL", "AWS", "Machine Learning", "C++"]
    
    # Create 50 students
    for i in range(1, 51):
        email = f"student{i}@example.com"
        pwd = auth.get_password_hash("password123")
        
        user = models.User(
            email=email,
            password_hash=pwd,
            role="student",
            college_id="bput_college_1"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        student = models.Student(
            user_id=user.id,
            name=f"Student {i}",
            branch=random.choice(branches),
            cgpa=round(random.uniform(6.0, 9.8), 2),
            aptitude_score=round(random.uniform(40, 95), 1),
            communication_score=round(random.uniform(40, 95), 1),
            interview_score=round(random.uniform(40, 95), 1),
            college_id="bput_college_1"
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        
        # Add random skills
        num_skills = random.randint(2, 5)
        selected_skills = random.sample(skills, num_skills)
        for skill in selected_skills:
            student_skill = models.StudentSkill(
                student_id=student.id,
                skill_name=skill,
                proficiency=random.randint(40, 95)
            )
            db.add(student_skill)
            
        # Add random project
        if random.random() > 0.3:
            project = models.Project(
                student_id=student.id,
                title=f"Project in {random.choice(selected_skills)}",
                description="A comprehensive project demonstrating core skills."
            )
            db.add(project)
            
    db.commit()
    print("Seeded 50 synthetic students.")
    db.close()

if __name__ == "__main__":
    # Ensure tables exist
    database.Base.metadata.create_all(bind=database.engine)
    run_seed()
