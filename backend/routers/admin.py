"""Placement Command Center: explicit admin, tenant and approval boundaries."""
from fastapi import APIRouter, Depends, Query
from auth import admin_session
from engines import analytics, scheduling, support
from schemas import (AnalyticsResponse, SchedulingBoard, ScheduleInput, SlotProposal, ScheduleResponse,
    ScheduleReviewInput, ScheduleRecheckInput, InterviewStatusInput, InterviewResponse,
    SupportReport, SupportRunInput, SupportReviewInput)

router = APIRouter(prefix="/admin", tags=["Placement Command Center"])

@router.get("/analytics/overview", response_model=AnalyticsResponse)
def overview(context=Depends(admin_session)):
    return analytics.overview(*context)

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
