import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import SessionLocal
from .. import models, schemas
from .auth import get_current_user

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
    from ..engines import matching
    matches = matching.run_matching(job_id=job_id, db=db, payload=payload)
    return matches
