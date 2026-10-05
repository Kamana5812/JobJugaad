"""Authenticated student resources; JWT tenant and ownership scope every operation."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from auth import student_session, owned_student
from engines.profile import profile_response, save_profile, update_fields
from engines.resume import extract_resume, MAX_BYTES
from schemas import ProfileResponse, ProfileUpdate, ReadinessResponse, ResumeResponse, AssessmentList
from engines import assessments

router = APIRouter(prefix="/students", tags=["Students"])

from schemas import ResumeSuggestions, TextEvidence
from engines import resume_fields, semantic

@router.get('/{student_id}/resume/suggestions', response_model=ResumeSuggestions)
def resume_suggestions(student_id: int, context=Depends(student_session)):
    session, user = context
    student = owned_student(session, user, student_id)
    return resume_fields.suggest(student.resume_text or '')

@router.post('/{student_id}/semantic-match/{job_id}', response_model=TextEvidence)
def semantic_match(student_id: int, job_id: int, context=Depends(student_session)):
    from models import Job, Company
    from sqlalchemy import select
    from engines.accounts import approved_scope
    session, user = context
    student = owned_student(session, user, student_id)
    job = session.scalar(select(Job).join(Company, (Company.id == Job.company_id) & (Company.college_id == Job.college_id)).where(
        Job.college_id == user.college_id, Company.college_id == user.college_id, Job.id == job_id,
        Job.is_open.is_(True), approved_scope(Company.recruiter_user_id, user.college_id, 'recruiter')))
    if job is None:
        raise HTTPException(404, 'Active college drive not found.')
    from engines.auth_limits import consume
    consume(user.college_id, str(user.id), 'semantic')
    return semantic.compare(job.description, profile_response(session, student))

@router.get('/{student_id}/assessments', response_model=AssessmentList)
def assessment_list(student_id: int, offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50), context=Depends(student_session)):
    session, user = context
    owned_student(session, user, student_id)
    return assessments.list_records(session, user, student_id, offset, limit)

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

from fastapi import Query
from engines import offers
from schemas import OfferList, OfferResponse, OfferStudentAction

@router.get("/{student_id}/offers", response_model=OfferList)
def offer_list(student_id:int,offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50),context=Depends(student_session)):
    session,user=context
    owned_student(session,user,student_id)
    return offers.list_offers(session,user,offset,limit)

@router.post("/{student_id}/offers/{offer_id}/actions", response_model=OfferResponse)
def offer_action(student_id:int,offer_id:int,payload:OfferStudentAction,context=Depends(student_session)):
    session,user=context
    owned_student(session,user,student_id)
    return offers.student_action(session,user,offer_id,payload)


from engines import placement_model
from schemas import PlacementModelInput, PlacementModelResponse

@router.get("/{student_id}/placement-model", response_model=PlacementModelResponse)
def get_placement_model(student_id: int, context=Depends(student_session)):
    session, user = context
    return placement_model.profile_response(session, owned_student(session, user, student_id))

@router.put("/{student_id}/placement-model", response_model=PlacementModelResponse)
def save_placement_model(student_id: int, payload: PlacementModelInput, context=Depends(student_session)):
    session, user = context
    return placement_model.profile_response(session, owned_student(session, user, student_id), payload)


from engines import btech_model
from schemas import BTechModelInput, BTechModelResponse

@router.get("/{student_id}/btech-placement-model", response_model=BTechModelResponse)
def get_btech_model(student_id: int, context=Depends(student_session)):
    session, user = context
    return btech_model.profile_response(session, owned_student(session,user,student_id))

@router.put("/{student_id}/btech-placement-model", response_model=BTechModelResponse)
def save_btech_model(student_id: int, payload: BTechModelInput, context=Depends(student_session)):
    session, user = context
    return btech_model.profile_response(session, owned_student(session,user,student_id),payload)


from typing import Literal
from engines.opportunities import student_opportunities
from schemas import StudentOpportunities

@router.get("/{student_id}/opportunities", response_model=StudentOpportunities)
def opportunities(student_id: int, status: Literal["eligible", "excluded", "all"] = "eligible",
    offset: int = Query(0, ge=0), limit: int = Query(3, ge=1, le=20),
    target_job_id: int | None = Query(None, ge=1), context=Depends(student_session)):
    session, user = context
    return student_opportunities(session, owned_student(session, user, student_id),
        status, offset, limit, target_job_id)


from engines import applications
from models import Application
from schemas import ApplicationSubmit, ApplicationAction, ApplicationResponse, ApplicationList

@router.post("/{student_id}/applications", response_model=ApplicationResponse, status_code=201)
def submit_application(student_id: int, payload: ApplicationSubmit, context=Depends(student_session)):
    session, user = context
    return applications.submit(session, user, owned_student(session, user, student_id), payload)

@router.get("/{student_id}/applications", response_model=ApplicationList)
def student_applications(student_id: int, offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50), context=Depends(student_session)):
    session, user = context
    student = owned_student(session, user, student_id)
    return applications.listing(session, user.college_id, Application.student_id == student.id, offset, limit)

@router.post("/{student_id}/applications/{application_id}/withdraw", response_model=ApplicationResponse)
def withdraw_application(student_id: int, application_id: int, payload: ApplicationAction, context=Depends(student_session)):
    session, user = context
    student = owned_student(session, user, student_id)
    return applications.action(session, user, application_id, Application.student_id == student.id, payload, withdraw=True)


from schemas import InterviewListResponse
from engines.interviews import interviews_for_student

@router.get("/{student_id}/interviews", response_model=InterviewListResponse)
def student_interviews(student_id: int, offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50), context=Depends(student_session)):
    session, user = context
    return interviews_for_student(session, owned_student(session, user, student_id), offset, limit)

from engines import calendar_constraints
from schemas import (CalendarConstraintList, CalendarConstraintResponse, StudentAvailabilityInput,
    CalendarCancelInput)

@router.get("/{student_id}/availability", response_model=CalendarConstraintList)
def availability_list(student_id: int, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50), context=Depends(student_session)):
    session, user = context
    student = owned_student(session, user, student_id)
    return calendar_constraints.constraints_list(session, user.college_id, offset, limit, student.id)

@router.post("/{student_id}/availability", response_model=CalendarConstraintResponse, status_code=201)
def declare_availability(student_id: int, payload: StudentAvailabilityInput, context=Depends(student_session)):
    session, user = context
    return calendar_constraints.create_student_availability(session, user, owned_student(session, user, student_id), payload)

@router.put("/{student_id}/availability/{constraint_id}/cancel", response_model=CalendarConstraintResponse)
def cancel_availability(student_id: int, constraint_id: int, payload: CalendarCancelInput, context=Depends(student_session)):
    session, user = context
    student = owned_student(session, user, student_id)
    return calendar_constraints.cancel_constraint(session, user, constraint_id, payload, student.id)
