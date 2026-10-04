"""Placement Command Center: explicit admin, tenant and approval boundaries."""
from typing import Literal
from fastapi import APIRouter, Depends, Query
from auth import admin_session
from engines import analytics, scheduling, support
from engines import post_selection
from schemas import (AnalyticsResponse, SchedulingBoard, ScheduleInput, SlotProposal, ScheduleResponse,
    ScheduleReviewInput, ScheduleRecheckInput, InterviewStatusInput, InterviewResponse,
    SupportReport, SupportRunInput, SupportReviewInput, PostSelectionAnalytics)

router = APIRouter(prefix="/admin", tags=["Placement Command Center"])

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
