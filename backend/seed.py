import asyncio
from .database import AsyncSessionLocal, engine
from sqlalchemy import select
from . import models, auth

async def create_demo_data():
    async with AsyncSessionLocal() as session:
        # Ensure tables are created
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        # Create a demo student if none exists
        result = await session.execute(select(models.User).where(models.User.email == "demo@example.com"))
        existing = result.scalar_one_or_none()
        if not existing:
            hashed = auth.get_password_hash("demo123")
            user = models.User(email="demo@example.com", password_hash=hashed, role="student")
            session.add(user)
            await session.flush()
            student = models.Student(
                user_id=user.id,
                name="Demo Student",
                branch="CSE",
                cgpa=8.5,
                backlog_count=0,
                aptitude_score=70,
                communication_score=65,
                interview_score=75,
            )
            session.add(student)
            await session.commit()
        # Create a demo recruiter if none exists
        result = await session.execute(select(models.User).where(models.User.email == "recruiter@example.com"))
        existing_rec = result.scalar_one_or_none()
        if not existing_rec:
            hashed = auth.get_password_hash("recruiter123")
            recruiter_user = models.User(email="recruiter@example.com", password_hash=hashed, role="recruiter")
            session.add(recruiter_user)
            await session.flush()
            # Create a company for this recruiter
            company = models.Company(name="DemoCo", recruiter_id=recruiter_user.id)
            session.add(company)
            await session.commit()

if __name__ == "__main__":
    asyncio.run(create_demo_data())
