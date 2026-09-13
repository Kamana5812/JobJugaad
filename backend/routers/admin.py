import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from backend.database import SessionLocal
from backend import models, schemas
from backend.routers.auth import get_current_user
from backend.engines import at_risk

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_admin(payload: dict = Depends(get_current_user)):
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload

@router.get("/analytics", response_model=schemas.AdminAnalytics)
def get_analytics(db: Session = Depends(get_db), payload: dict = Depends(require_admin)):
    college_id = payload["college_id"]
    
    # KPI metrics
    total_students = db.query(models.Student).filter(models.Student.college_id == college_id).count()
    total_drives = db.query(models.Job).filter(models.Job.college_id == college_id).count()
    total_matches = db.query(models.Match).filter(models.Match.college_id == college_id).count()
    total_interviews = db.query(models.Interview).filter(models.Interview.college_id == college_id).count()
    
    # Matches by branch for Recharts
    # Assuming students have a branch, and matches belong to students.
    # To keep it simple, we join matches and students and group by student branch
    matches_by_branch_query = db.query(
        models.Student.branch, func.count(models.Match.id).label("count")
    ).join(
        models.Match, models.Student.id == models.Match.student_id
    ).filter(
        models.Match.college_id == college_id
    ).group_by(models.Student.branch).all()
    
    matches_by_branch = [
        {"name": row[0] or "Unknown", "value": row[1]}
        for row in matches_by_branch_query
    ]
    
    return schemas.AdminAnalytics(
        total_students=total_students,
        total_drives=total_drives,
        total_matches=total_matches,
        total_interviews=total_interviews,
        matches_by_branch=matches_by_branch
    )

@router.get("/at-risk", response_model=List[schemas.AtRiskStudent])
def get_at_risk_students(db: Session = Depends(get_db), payload: dict = Depends(require_admin)):
    college_id = payload["college_id"]
    students = db.query(models.Student).filter(models.Student.college_id == college_id).all()
    
    at_risk_list = []
    for student in students:
        result = at_risk.evaluate_student(student, db)
        if result["is_at_risk"]:
            at_risk_list.append(schemas.AtRiskStudent(**result))
            
    return at_risk_list
