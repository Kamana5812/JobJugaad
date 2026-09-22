"""Authenticated student resources; JWT tenant and ownership scope every operation."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from auth import student_session, owned_student
from engines.profile import profile_response, save_profile, update_fields
from engines.resume import extract_resume, MAX_BYTES
from schemas import ProfileResponse, ProfileUpdate, ReadinessResponse, ResumeResponse

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/{student_id}", response_model=ProfileResponse)
def get_profile(student_id: int, context=Depends(student_session)):
    session, user = context
    return profile_response(session, owned_student(session, user, student_id))

@router.put("/{student_id}", response_model=ProfileResponse)
def update_profile(student_id: int, payload: ProfileUpdate, context=Depends(student_session)):
    session, user = context
    return save_profile(session, owned_student(session, user, student_id), payload)

@router.get("/{student_id}/readiness", response_model=ReadinessResponse)
def readiness(student_id: int, context=Depends(student_session)):
    session, user = context
    return profile_response(session, owned_student(session, user, student_id)).readiness

@router.post("/{student_id}/resume", response_model=ResumeResponse)
def upload_resume(student_id: int, file: UploadFile = File(...), context=Depends(student_session)):
    session, user = context
    student = owned_student(session, user, student_id)
    try:
        content = file.file.read(MAX_BYTES + 1)
    finally:
        file.file.close()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Please upload a PDF no larger than 5 MB.")
    extracted = extract_resume(content)
    update_fields(session, student, {"resume_text": extracted})
    return ResumeResponse(detail="Resume text saved. Review it and update your profile evidence below.",
        extracted_characters=len(extracted), profile=profile_response(session, student))
