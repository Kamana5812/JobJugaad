import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import SessionLocal
from backend import models, schemas
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/recruiter", tags=["recruiter"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/companies", response_model=schemas.CompanyRead)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    if payload.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can create a company")
    # Ensure recruiter doesn't already have a company
    existing = db.query(models.Company).filter(models.Company.recruiter_user_id == payload["user_id"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Recruiter already has a company")
    new_company = models.Company(
        recruiter_user_id=payload["user_id"],
        name=company.name,
        industry=company.industry,
        college_id=payload["college_id"],
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company

@router.get("/companies/me", response_model=schemas.CompanyRead)
def get_my_company(db: Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    if payload.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can view a company")
    company = db.query(models.Company).filter(models.Company.recruiter_user_id == payload["user_id"]).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found for this recruiter")
    return company

@router.post("/jobs", response_model=schemas.JobRead)
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    if payload.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can create jobs")
    company = db.query(models.Company).filter(models.Company.recruiter_user_id == payload["user_id"]).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found for recruiter")
    new_job = models.Job(
        company_id=company.id,
        title=job.title,
        ctc=job.ctc,
        min_cgpa=job.min_cgpa,
        eligible_branches=job.eligible_branches,
        required_skills=job.required_skills,
        college_id=payload["college_id"],
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@router.get("/jobs/{job_id}", response_model=schemas.JobRead)
def get_job(job_id: str, db: Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Recruiter may only view jobs belonging to their own company
    if payload.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can view jobs")
    if job.company.recruiter_user_id != payload["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied for this job")
    return job

# Matching endpoint – runs the matching engine and returns matches
@router.get("/jobs/{job_id}/matches", response_model=List[schemas.MatchRead])
def get_matches(job_id: str, db: Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    # Ensure the caller belongs to the same college (RLS ensures) and is a recruiter
    if payload.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can run matching")
    from backend.engines import matching
    matches = matching.run_matching(job_id=job_id, db=db, payload=payload)
    return matches

@router.post("/matches/{match_id}/override", response_model=schemas.MatchRead)
def override_match(match_id: str, override: schemas.MatchOverride, db: Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    if payload.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can override matches")
    
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    # Verify the match belongs to a job owned by this recruiter
    job = db.query(models.Job).filter(models.Job.id == match.job_id).first()
    if not job or job.company.recruiter_user_id != payload["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied for this match")
        
    if override.status not in ["promoted", "rejected", "none"]:
        raise HTTPException(status_code=400, detail="Invalid override status")
        
    match.override_status = override.status if override.status != "none" else None
    db.commit()
    db.refresh(match)
    return match

@router.post("/interviews", response_model=schemas.InterviewRead)
def schedule_interview(interview: schemas.InterviewCreate, db: Session = Depends(get_db), payload: dict = Depends(get_current_user)):
    if payload.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Only recruiters can schedule interviews")
        
    job = db.query(models.Job).filter(models.Job.id == interview.job_id).first()
    if not job or job.company.recruiter_user_id != payload["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied for this job")
        
    from datetime import datetime
    preferred_start = datetime.fromisoformat(interview.preferred_start.replace("Z", "+00:00"))
    
    from backend.engines import scheduling
    try:
        start_time, end_time = scheduling.propose_schedule(
            job_id=str(interview.job_id),
            student_id=str(interview.student_id),
            preferred_start=preferred_start,
            duration_minutes=interview.duration_minutes,
            venue=interview.venue,
            panel=interview.panel,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    new_interview = models.Interview(
        job_id=job.id,
        student_id=interview.student_id,
        start_time=start_time,
        end_time=end_time,
        venue=interview.venue,
        panel=interview.panel,
        college_id=payload["college_id"]
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    # Convert datetime to string for response model
    new_interview.start_time = new_interview.start_time.isoformat()
    new_interview.end_time = new_interview.end_time.isoformat()
    return new_interview
