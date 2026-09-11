from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database import get_db
import models, schemas, auth

router = APIRouter()

# Helper to get current recruiter user
async def get_current_recruiter(db: AsyncSession = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if not user or user.role != "recruiter":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recruiter access required")
    return user

@router.post("/company", response_model=schemas.CompanySchema)
async def create_company(company: schemas.CompanyCreate, recruiter: models.User = Depends(get_current_recruiter), db: AsyncSession = Depends(get_db)):
    # Ensure a company with this name doesn't already exist for this recruiter
    result = await db.execute(select(models.Company).where(
        and_(models.Company.name == company.name, models.Company.recruiter_id == recruiter.id)
    ))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company already exists")
    db_company = models.Company(name=company.name, recruiter_id=recruiter.id)
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)
    return db_company

@router.post("/jobs", response_model=schemas.JobOut)
async def create_job(job: schemas.JobCreate, recruiter: models.User = Depends(get_current_recruiter), db: AsyncSession = Depends(get_db)):
    # Ensure recruiter has a company; create a default one if none
    result = await db.execute(select(models.Company).where(models.Company.recruiter_id == recruiter.id))
    company = result.scalar_one_or_none()
    if not company:
        # Auto‑create a company using recruiter email as name
        company = models.Company(name=recruiter.email, recruiter_id=recruiter.id)
        db.add(company)
        await db.commit()
        await db.refresh(company)
    db_job = models.Job(
        company_id=company.id,
        title=job.title,
        ctc=job.ctc,
        min_cgpa=job.min_cgpa,
        eligible_branches=job.eligible_branches,
        required_skills=job.required_skills,
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    # Return with nested company info
    return schemas.JobOut.from_orm(db_job)

@router.get("/jobs/{job_id}/match", response_model=list[schemas.MatchOut])
async def match_job(job_id: int, recruiter: models.User = Depends(get_current_recruiter), db: AsyncSession = Depends(get_db)):
    # Fetch job
    result = await db.execute(select(models.Job).where(models.Job.id == job_id, models.Job.company.has(models.Company.recruiter_id == recruiter.id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    # Parse eligibility criteria
    allowed_branches = [b.strip() for b in job.eligible_branches.split(',') if b.strip()]
    required_skills = [s.strip().lower() for s in job.required_skills.split(',') if s.strip()]
    # Fetch eligible students
    stmt = select(models.Student).where(
        models.Student.cgpa >= job.min_cgpa,
        models.Student.branch.in_(allowed_branches)
    )
    result = await db.execute(stmt)
    students = result.scalars().all()
    matches = []
    for student in students:
        # Compute skill match sum
        skill_sum = 0
        for skill in student.skills:
            if skill.skill_name.lower() in required_skills:
                skill_sum += skill.proficiency
        # Include readiness score as additional factor
        total_score = skill_sum + (student.readiness_score or 0)
        matches.append({
            "student_id": student.id,
            "name": student.name,
            "score": total_score,
            "breakdown": {"skill_sum": skill_sum, "readiness": student.readiness_score or 0},
        })
    # Sort descending by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches
