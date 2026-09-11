from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
import models, schemas, auth, engines
from engines.readiness import calculate_readiness
import pdfplumber
import io


router = APIRouter()

# Dependency to get the current logged‑in user via JWT
async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email: str = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get("/me", response_model=schemas.StudentOut)
async def get_my_profile(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    await db.refresh(current_user.student)  # ensure relationships are loaded
    return current_user.student

@router.post("/me/resume")
async def upload_resume(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")
    # Read file into memory and extract text using pdfplumber
    contents = await file.read()
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    # Store extracted text on the student record
    current_user.student.resume_text = text
    db.add(current_user.student)
    await db.commit()
    return {"detail": "Resume uploaded and processed successfully"}

@router.get("/me/readiness", response_model=schemas.ReadinessOut)
async def get_readiness(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    # Refresh to get latest related data (skills, projects, etc.)
    await db.refresh(current_user.student)
    result = calculate_readiness(current_user.student)
    return result
