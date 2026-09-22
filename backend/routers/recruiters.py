"""Talent Finder routes; tenant/role/ownership checks precede every operation."""
from typing import Literal
from fastapi import APIRouter, Depends, Query
from auth import recruiter_session
from sqlalchemy import update
from models import Company
from engines import talent
from schemas import CompanyInput, CompanyResponse, JobInput, JobResponse, MatchSummary, MatchResults, OverrideInput, CandidateResponse

router = APIRouter(prefix="/recruiters", tags=["Talent Finder"])


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
