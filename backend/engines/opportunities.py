"""Owned, read-only student view; reuse the existing weighted rule unchanged.

No match snapshots, shortlist overrides or recruiter audit notes are written or
exposed here. This is a preparation comparison, not a recruiter decision or an
application. Compute before pagination so ranking covers every college drive.
"""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from models import Job, Company
from engines.profile import collections
from engines.matching import calculate_match
from schemas import StudentOpportunity, StudentOpportunities, OpportunityRole


def student_opportunities(session, student, status, offset, limit, target_job_id=None):
    evidence = collections(session, student)
    # Both application filters remain explicit, independently of FORCE RLS.
    rows = session.execute(select(Job, Company).join(Company,
        (Company.id == Job.company_id) & (Company.college_id == Job.college_id)).where(
        Job.college_id == student.college_id, Company.college_id == student.college_id)).all()
    results = []
    for job, company in rows:
        calculation = calculate_match(student, evidence["skills"], evidence["projects"],
            evidence["certifications"], job)
        results.append(StudentOpportunity(**calculation.model_dump(), job_id=job.id,
            title=job.title, company_name=company.name, ctc=float(job.ctc), min_cgpa=job.min_cgpa,
            max_backlogs=job.max_backlogs, eligible_branches=job.eligible_branches,
            min_match_score=job.min_match_score))
    results.sort(key=lambda result: (-result.match_score, result.job_id))
    eligible = [result for result in results if result.eligible]
    excluded = [result for result in results if not result.eligible]
    target = next((result for result in results if result.job_id == target_job_id), None)
    if target_job_id is not None and target is None:
        raise HTTPException(404, "Drive not found in your college.")
    if target is None:
        target = next(iter(eligible or results), None)
    visible = results if status == "all" else eligible if status == "eligible" else excluded
    return StudentOpportunities(items=visible[offset:offset + limit], target=target,
        roles=[OpportunityRole(job_id=result.job_id, title=result.title,
            company_name=result.company_name) for result in results], total=len(visible),
        eligible_count=len(eligible), excluded_count=len(excluded), offset=offset, limit=limit,
        calculated_at=datetime.now(timezone.utc), explanation=(
            "Fresh comparison of your saved profile with recorded college drives using the existing "
            "keyword/weighted rule. Eligible roles and excluded roles are separate views; each is "
            "sorted by descending score, ties by drive ID. This is not a recruiter shortlist, an "
            "application or an offer. Recruiter reviews and overrides are separate and unchanged."))
