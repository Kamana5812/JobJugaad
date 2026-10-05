"""Placement Command Center: explicit admin, tenant and approval boundaries."""
from typing import Literal
from fastapi import APIRouter, Depends, Query
from auth import admin_session
from engines import analytics, scheduling, support
from engines import post_selection
from engines import assessments
from schemas import (AnalyticsResponse, SchedulingBoard, ScheduleInput, SlotProposal, ScheduleResponse,
    ScheduleReviewInput, ScheduleRecheckInput, InterviewStatusInput, InterviewResponse,
    SupportReport, SupportRunInput, SupportReviewInput, PostSelectionAnalytics,
    AssessmentInput, AssessmentWithdrawal, AssessmentResponse, AssessmentList)

router = APIRouter(prefix="/admin", tags=["Placement Command Center"])

from schemas import TextEvidence
from engines import semantic

@router.post('/jobs/{job_id}/applications/{application_id}/semantic', response_model=TextEvidence)
def staff_semantic(job_id: int, application_id: int, context=Depends(admin_session)):
    from engines import applications, talent
    session, user = context
    job = talent.college_job(session, user, job_id)
    profile = applications.review_profile(session, user, job, application_id)
    from engines.auth_limits import consume
    consume(user.college_id, str(user.id), 'semantic')
    return semantic.compare(job.description, profile)

from engines import demand
from schemas import DemandReport, ReminderRunResponse

@router.post('/reminders/run', response_model=ReminderRunResponse)
def due_reminders(context=Depends(admin_session)):
    from engines.reminders import generate
    session, user = context
    count = generate(session, user.college_id)
    return {'eligible_bookings_processed': count, 'explanation': 'Due in-app reminders were checked for this college. Duplicate event/bucket keys are ignored. This count is processed bookings, not delivered emails or read receipts.'}

@router.get('/analytics/demand', response_model=DemandReport)
def college_demand(context=Depends(admin_session)):
    return demand.report(*context)

from sqlalchemy import select
from models import Job, Application
from engines import talent, applications
from schemas import JobResponse, MatchResults, MatchSummary, OverrideInput, CandidateResponse, ApplicationList, ApplicationReview, ApplicationResponse
from schemas import ProfileResponse
from schemas import DriveStateInput
from schemas import StudentDirectory
from sqlalchemy import func, or_
from models import Student, User
from engines.profile import profile_response
from fastapi import HTTPException

@router.get('/students', response_model=StudentDirectory)
def student_directory(query: str = Query('', max_length=100), offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50), context=Depends(admin_session)):
    session, user = context
    filters = [Student.college_id == user.college_id, User.college_id == user.college_id, User.role == 'student']
    if query.strip():
        escaped = query.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        pattern = '%' + escaped + '%'
        filters.append(or_(Student.name.ilike(pattern, escape='\\'), User.email.ilike(pattern, escape='\\')))
    join = (User.id == Student.user_id) & (User.college_id == Student.college_id)
    total = session.scalar(select(func.count()).select_from(Student).join(User, join).where(*filters))
    rows = session.execute(select(Student, User).join(User, join).where(*filters)
        .order_by(Student.id).offset(offset).limit(limit)).all()
    return {'items': [dict(id=s.id, user_id=u.id, name=s.name, branch=s.branch, email=u.email,
        restricted=u.disabled_at is not None) for s, u in rows], 'total': total, 'offset': offset, 'limit': limit}

@router.get('/students/{student_id}/profile', response_model=ProfileResponse)
def staff_student_profile(student_id: int, context=Depends(admin_session)):
    session, user = context
    student = session.scalar(select(Student).join(User,
        (User.id == Student.user_id) & (User.college_id == Student.college_id)).where(
        Student.college_id == user.college_id, User.college_id == user.college_id,
        User.role == 'student', Student.id == student_id))
    if student is None:
        raise HTTPException(404, 'Student profile not found in your college.')
    return profile_response(session, student)

@router.post('/jobs/{job_id}/state', response_model=JobResponse)
def college_drive_state(job_id: int, payload: DriveStateInput, context=Depends(admin_session)):
    session, user = context
    return talent.set_drive_state(session, user, talent.college_job(session, user, job_id, lock=True), payload)

@router.get('/jobs/{job_id}/applications/{application_id}/profile', response_model=ProfileResponse)
def college_application_profile(job_id: int, application_id: int, context=Depends(admin_session)):
    session, user = context
    return applications.review_profile(session, user, talent.college_job(session, user, job_id), application_id)

@router.get('/jobs', response_model=list[JobResponse])
def college_jobs(context=Depends(admin_session)):
    session, user = context
    return [talent.job_response(job) for job in session.scalars(select(Job).where(
        Job.college_id == user.college_id).order_by(Job.id.desc()))]

@router.post('/jobs/{job_id}/matching', response_model=MatchSummary)
def college_matching(job_id: int, context=Depends(admin_session)):
    session, user = context
    return talent.run_matching(session, talent.college_job(session, user, job_id, lock=True))

@router.get('/jobs/{job_id}/matches', response_model=MatchResults)
def college_matches(job_id: int, status: Literal['all', 'shortlisted', 'excluded'] = 'shortlisted',
    offset: int = Query(0, ge=0), limit: int = Query(5, ge=1, le=100), context=Depends(admin_session)):
    session, user = context
    return talent.match_results(session, talent.college_job(session, user, job_id), status, offset, limit)

@router.post('/jobs/{job_id}/matches/{match_id}/override', response_model=CandidateResponse)
def college_override(job_id: int, match_id: int, payload: OverrideInput, context=Depends(admin_session)):
    session, user = context
    return talent.override_match(session, user, talent.college_job(session, user, job_id, lock=True), match_id, payload)

@router.get('/jobs/{job_id}/applications', response_model=ApplicationList)
def college_applications(job_id: int, offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50), context=Depends(admin_session)):
    session, user = context
    job = talent.college_job(session, user, job_id)
    return applications.listing(session, user.college_id, Application.job_id == job.id, offset, limit)

@router.post('/jobs/{job_id}/applications/{application_id}/review', response_model=ApplicationResponse)
def college_application_review(job_id: int, application_id: int, payload: ApplicationReview, context=Depends(admin_session)):
    session, user = context
    job = talent.college_job(session, user, job_id)
    return applications.action(session, user, application_id, Application.job_id == job.id, payload)

@router.get('/assessments', response_model=AssessmentList)
def assessment_list(student_id: int | None = Query(None, gt=0), offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50), context=Depends(admin_session)):
    return assessments.list_records(*context, student_id, offset, limit)

@router.post('/assessments', response_model=AssessmentResponse, status_code=201)
def assessment_create(payload: AssessmentInput, context=Depends(admin_session)):
    return assessments.create(*context, payload)

@router.post('/assessments/{assessment_id}/withdraw', response_model=AssessmentResponse)
def assessment_withdraw(assessment_id: int, payload: AssessmentWithdrawal, context=Depends(admin_session)):
    return assessments.withdraw(*context, assessment_id, payload)

@router.get("/analytics/overview", response_model=AnalyticsResponse)
def overview(context=Depends(admin_session)):
    return analytics.overview(*context)

@router.get("/analytics/post-selection", response_model=PostSelectionAnalytics)
def post_selection_analytics(scope: Literal["recorded", "synthetic", "all"] = "recorded",
    job_id: int | None = Query(None, gt=0), offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50), context=Depends(admin_session)):
    return post_selection.report(*context, scope, job_id, offset, limit)

@router.get("/schedules", response_model=SchedulingBoard)
def calendar(context=Depends(admin_session)):
    return scheduling.calendar_board(*context)

@router.post("/schedules/check-conflict", response_model=SlotProposal)
def check(payload: ScheduleInput, context=Depends(admin_session)):
    return scheduling.check_schedule(*context, payload)

@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
def propose(payload: ScheduleInput, context=Depends(admin_session)):
    return scheduling.create_proposal(*context, payload)

@router.post("/schedules/{schedule_id}/review", response_model=ScheduleResponse)
def review(schedule_id: int, payload: ScheduleReviewInput, context=Depends(admin_session)):
    return scheduling.review_proposal(*context, schedule_id, payload)

@router.post("/schedules/{schedule_id}/recheck", response_model=ScheduleResponse)
def recheck(schedule_id: int, payload: ScheduleRecheckInput, context=Depends(admin_session)):
    return scheduling.recheck_proposal(*context, schedule_id, payload)

@router.put("/interviews/{interview_id}/status", response_model=InterviewResponse)
def interview_status(interview_id: int, payload: InterviewStatusInput, context=Depends(admin_session)):
    return scheduling.change_interview_status(*context, interview_id, payload)

@router.get("/support", response_model=SupportReport)
def support_list(job_id: int = Query(gt=0), context=Depends(admin_session)):
    return support.report(*context, job_id)

@router.post("/support/run", response_model=SupportReport)
def support_run(payload: SupportRunInput, context=Depends(admin_session)):
    return support.run_support(*context, payload.job_id)

@router.post("/support/{prediction_id}/review", response_model=SupportReport)
def support_review(prediction_id: int, payload: SupportReviewInput, context=Depends(admin_session)):
    return support.review_support(*context, prediction_id, payload)

# Offer issuance and verification remain explicit human actions.
from engines import offers
from schemas import OfferCreate, OfferAdminUpdate, OfferResponse, OfferList, OfferCandidateList

@router.get("/offers", response_model=OfferList)
def offer_list(offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50),context=Depends(admin_session)):
    return offers.list_offers(*context,offset,limit)

@router.get("/offers/eligible-interviews", response_model=OfferCandidateList)
def offer_candidates(search:str=Query("",max_length=100),offset:int=Query(0,ge=0),
                     limit:int=Query(20,ge=1,le=50),context=Depends(admin_session)):
    return offers.candidates(*context,search,offset,limit)

@router.post("/offers", response_model=OfferResponse,status_code=201)
def create_offer(payload:OfferCreate,context=Depends(admin_session)):
    return offers.create_offer(*context,payload)

@router.put("/offers/{offer_id}", response_model=OfferResponse)
def update_offer(offer_id:int,payload:OfferAdminUpdate,context=Depends(admin_session)):
    return offers.admin_update(*context,offer_id,payload)


from engines import accounts
from schemas import AccessQueue, AccessReviewInput, AccountAccessResponse

from engines import calendar_constraints
from schemas import (CalendarSettingsResponse, CalendarSettingsInput, CalendarConstraintInput,
    CalendarConstraintList, CalendarConstraintResponse, CalendarCancelInput)

@router.get("/calendar/settings", response_model=CalendarSettingsResponse)
def calendar_settings(context=Depends(admin_session)):
    session, user = context
    return calendar_constraints.settings_for(session, user.college_id)

@router.put("/calendar/settings", response_model=CalendarSettingsResponse)
def update_calendar_settings(payload: CalendarSettingsInput, context=Depends(admin_session)):
    return calendar_constraints.save_settings(*context, payload)

@router.get("/calendar/constraints", response_model=CalendarConstraintList)
def calendar_constraints_list(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50), context=Depends(admin_session)):
    session, user = context
    return calendar_constraints.constraints_list(session, user.college_id, offset, limit)

@router.post("/calendar/constraints", response_model=CalendarConstraintResponse, status_code=201)
def add_calendar_constraint(payload: CalendarConstraintInput, context=Depends(admin_session)):
    return calendar_constraints.create_constraint(*context, payload)

@router.put("/calendar/constraints/{constraint_id}/cancel", response_model=CalendarConstraintResponse)
def cancel_calendar_constraint(constraint_id: int, payload: CalendarCancelInput, context=Depends(admin_session)):
    return calendar_constraints.cancel_constraint(*context, constraint_id, payload)

@router.get("/accounts", response_model=AccessQueue)
def account_queue(status: Literal["pending", "approved", "rejected"] = "pending", offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50), context=Depends(admin_session)):
    return accounts.queue(*context, status, offset, limit)

@router.post("/accounts/{access_id}/review", response_model=AccountAccessResponse)
def review_account(access_id: int, payload: AccessReviewInput, context=Depends(admin_session)):
    return accounts.review(*context, access_id, payload)
