from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import database, models, schemas, auth
from engines.readiness import calculate_readiness_score
import pdfplumber
import io

router = APIRouter(prefix="/students", tags=["students"])

@router.get("/{student_id}/profile", response_model=schemas.StudentProfile)
def get_student_profile(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Optional: verify current_user has access to this student
    if current_user.role == "student" and student.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this profile")
        
    return student

@router.get("/{student_id}/readiness", response_model=schemas.ReadinessResponse)
def get_readiness_score(student_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    readiness_data = calculate_readiness_score(student)
    
    # Save the updated readiness score to db
    student.readiness_score = readiness_data["score"]
    db.commit()
    
    return readiness_data

@router.post("/{student_id}/resume")
async def upload_resume(student_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    if current_user.role == "student" and student.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
        
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    try:
        content = await file.read()
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() + "\n"
                
        student.resume_text = extracted_text
        db.commit()
        
        return {"detail": "Resume uploaded and parsed successfully", "text_length": len(extracted_text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")
