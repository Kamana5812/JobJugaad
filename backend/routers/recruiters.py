"""Talent Finder routes; tenant/role/ownership checks precede every operation."""
from typing import Literal
from fastapi import APIRouter, Depends, Query
from auth import recruiter_session
from sqlalchemy import update
from models import Company
from engines import talent
from schemas import CompanyInput, CompanyResponse, JobInput, JobResponse, MatchSummary, MatchResults, OverrideInput, CandidateResponse

router = APIRouter(prefix="/recruiters", tags=["Talent Finder"])

from schemas import TextEvidence
from engines import semantic

@router.post('/jobs/{job_id}/applications/{application_id}/semantic', response_model=TextEvidence)
def application_semantic(job_id: int, application_id: int, context=Depends(recruiter_session)):
    from engines.applications import review_profile
    session, user = context
    job = talent.owned_job(session, user, job_id)
    profile = review_profile(session, user, job, application_id)
    from engines.auth_limits import consume
    consume(user.college_id, str(user.id), 'semantic')
    return semantic.compare(job.description, profile)

from engines import demand
from schemas import DemandReport

@router.get('/analytics/demand', response_model=DemandReport)
def hiring_demand(context=Depends(recruiter_session)):
    return demand.report(*context)

from schemas import DescriptionInput, DescriptionReview
from schemas import DriveStateInput
from engines.job_text import review_description

@router.post('/jobs/description/review', response_model=DescriptionReview)
def description_review(payload: DescriptionInput, context=Depends(recruiter_session)):
    return review_description(payload.description)

@router.post('/jobs/{job_id}/state', response_model=JobResponse)
def drive_state(job_id: int, payload: DriveStateInput, context=Depends(recruiter_session)):
    session, user = context
    return talent.set_drive_state(session, user, talent.owned_job(session, user, job_id, lock=True), payload)


@router.get("/company", response_model=CompanyResponse)
def company(context=Depends(recruiter_session)):
    session, user = context
    return talent.company_response(talent.owned_company(session, user))


@router.put("/company", response_model=CompanyResponse)
def update_company(payload: CompanyInput, context=Depends(recruiter_session)):
    session, user = context
    company = talent.owned_company(session, user)
    session.execute(update(Company).where(Company.id == company.id, Company.college_id == user.college_id,
        Company.recruiter_user_id == user.id).values(**payload.model_dump()))
    session.flush()
    return talent.company_response(company)


@router.get("/jobs", response_model=list[JobResponse])
def jobs(context=Depends(recruiter_session)):
    return talent.jobs_for_company(*context)


@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(payload: JobInput, context=Depends(recruiter_session)):
    return talent.create_job(*context, payload)


@router.post("/jobs/{job_id}/matching", response_model=MatchSummary)
def run_matching(job_id: int, context=Depends(recruiter_session)):
    session, user = context
    return talent.run_matching(session, talent.owned_job(session, user, job_id, lock=True))


@router.get("/jobs/{job_id}/matches", response_model=MatchResults)
def matches(job_id: int, status: Literal["all", "shortlisted", "excluded"] = "shortlisted",
            offset: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100),
            context=Depends(recruiter_session)):
    session, user = context
    return talent.match_results(session, talent.owned_job(session, user, job_id), status, offset, limit)


@router.post("/jobs/{job_id}/matches/{match_id}/override", response_model=CandidateResponse)
def override(job_id: int, match_id: int, payload: OverrideInput, context=Depends(recruiter_session)):
    session, user = context
    return talent.override_match(session, user, talent.owned_job(session, user, job_id, lock=True), match_id, payload)


from engines import applications
from models import Application
from schemas import ApplicationList, ApplicationResponse, ApplicationReview
from schemas import ProfileResponse

@router.get("/jobs/{job_id}/applications/{application_id}/profile", response_model=ProfileResponse)
def application_profile(job_id: int, application_id: int, context=Depends(recruiter_session)):
    session, user = context
    return applications.review_profile(session, user, talent.owned_job(session, user, job_id), application_id)

@router.get("/jobs/{job_id}/applications", response_model=ApplicationList)
def job_applications(job_id: int, offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50), context=Depends(recruiter_session)):
    session, user = context
    job = talent.owned_job(session, user, job_id)
    return applications.listing(session, user.college_id, Application.job_id == job.id, offset, limit)

@router.post("/jobs/{job_id}/applications/{application_id}/review", response_model=ApplicationResponse)
def review_application(job_id: int, application_id: int, payload: ApplicationReview, context=Depends(recruiter_session)):
    session, user = context
    job = talent.owned_job(session, user, job_id)
    return applications.action(session, user, application_id, Application.job_id == job.id, payload)
