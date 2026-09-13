import random
import uuid
from datetime import datetime
from faker import Faker
from backend.database import SessionLocal
from backend import models

fake = Faker()

def generate_student(college_id: str):
    # Create a user first (email/password)
    password = "password123"
    user = models.User(
        email=fake.unique.email(),
        password_hash="",  # will be replaced after hashing
        role="student",
        college_id=college_id,
    )
    # Actually hash password using passlib
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.password_hash = pwd_ctx.hash(password)
    return user

def seed(college_id: str = None, count: int = 50):
    if not college_id:
        college_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        for _ in range(count):
            user = generate_student(college_id)
            db.add(user)
            db.flush()  # get user.id
            student = models.Student(
                user_id=user.id,
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
            db.add(student)
        db.commit()
        print(f"✅ Seeded {count} synthetic student profiles for college {college_id}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
