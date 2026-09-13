'''Student related endpoints.
- `GET /students/{id}/profile` – returns student data (auth required).
- `POST /students/{id}/resume` – multipart PDF upload, extracts text via pdfplumber, stores in `resume_text`.
- `GET /students/{id}/readiness` – runs the readiness engine and returns score, band, breakdown, explanation.
All endpoints enforce that the `college_id` in the JWT matches the student's `college_id` (application‑level filter) and rely on PostgreSQL RLS for an extra safety layer.
'''

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import text
import pdfplumber
from io import BytesIO

from ..database import SessionLocal, engine
from .. import models, schemas, engines

router = APIRouter(prefix="/students", tags=["students"])

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

# Dependency to get DB session and set RLS "app.college_id" parameter
def get_db_and_set_rls(token: str = Depends(auth_scheme)):
    # Decode JWT
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        college_id = payload.get("college_id")
        if college_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    db = SessionLocal()
    try:
        # Set PostgreSQL session variable used by RLS policies
        db.execute(text("SET app.college_id = :cid"), {"cid": str(college_id)})
        yield db, payload
    finally:
        db.close()

def get_current_user(payload: dict = Depends(lambda token=Depends(auth_scheme): jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM]))):
    return payload

@router.get("/{student_id}", response_model=schemas.StudentRead)
def get_student(student_id: str, db_payload = Depends(get_db_and_set_rls)):
    db, token_payload = db_payload
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # Application‑level college check (redundant with RLS but required by RULES)
    if str(student.college_id) != token_payload["college_id"]:
        raise HTTPException(status_code=403, detail="Access denied for this college")
    return student

@router.post("/{student_id}/resume")
async def upload_resume(student_id: str, file: UploadFile = File(...), db_payload = Depends(get_db_and_set_rls)):
    db, token_payload = db_payload
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    # Read PDF content
    contents = await file.read()
    with pdfplumber.open(BytesIO(contents)) as pdf:
        text_pages = [page.extract_text() or "" for page in pdf.pages]
    extracted_text = "\n".join(text_pages)
    # Store in student record
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if str(student.college_id) != token_payload["college_id"]:
        raise HTTPException(status_code=403, detail="Access denied for this college")
    student.resume_text = extracted_text
    db.commit()
    return {"detail": "Resume parsed and stored"}

@router.get("/{student_id}/readiness", response_model=schemas.ReadinessResponse)
def get_readiness(student_id: str, db_payload = Depends(get_db_and_set_rls)):
    db, token_payload = db_payload
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if str(student.college_id) != token_payload["college_id"]:
        raise HTTPException(status_code=403, detail="Access denied for this college")
    # Run readiness engine
    result = engines.readiness.calculate_readiness(student)
    return result

@router.get("/me", response_model=schemas.StudentRead)
def get_my_student(db_payload = Depends(get_db_and_set_rls)):
    db, token_payload = db_payload
    user_id = token_payload["user_id"]
    student = db.query(models.Student).filter(models.Student.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found for this user")
    return student
