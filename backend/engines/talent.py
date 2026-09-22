"""Tenant-scoped recruiter operations and auditable human shortlist decisions."""
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from models import Company, Job, Match, MatchOverride, Student, StudentSkill, Project, Certification
from schemas import CompanyResponse, JobResponse, MatchCalculation, CandidateResponse, OverrideResponse, MatchSummary, MatchResults
from engines.matching import calculate_match


def owned_company(session, user):
    company = session.scalar(select(Company).where(Company.college_id == user.college_id, Company.recruiter_user_id == user.id))
    if company is None:
        raise HTTPException(404, "Company profile not found.")
    return company


def company_response(company):
    return CompanyResponse.model_validate(company, from_attributes=True)


def owned_job(session, user, job_id, lock=False):
    company = owned_company(session, user)
    query = select(Job).where(Job.college_id == user.college_id, Job.company_id == company.id, Job.id == job_id)
    job = session.scalar(query.with_for_update() if lock else query)
    if job is None:
        raise HTTPException(404, "Drive not found.")
    return job


def job_response(job):
    return JobResponse.model_validate(job, from_attributes=True)


def jobs_for_company(session, user):
    company = owned_company(session, user)
    return [job_response(j) for j in session.scalars(select(Job).where(
        Job.college_id == user.college_id, Job.company_id == company.id).order_by(Job.id.desc()))]


def create_job(session, user, payload):
    company = owned_company(session, user)
    job = Job(college_id=user.college_id, company_id=company.id, **payload.model_dump())
    session.add(job)
    session.flush()
    return job_response(job)


def run_matching(session, job):
    # Caller locks the owned job row; concurrent reruns and overrides serialize.
    college = job.college_id
    students = session.scalars(select(Student).where(Student.college_id == college).order_by(Student.id)).all()
    grouped = []
    for model in (StudentSkill, Project, Certification):
        rows = defaultdict(list)
        for row in session.scalars(select(model).where(model.college_id == college)):
            rows[row.student_id].append(row)
        grouped.append(rows)
    existing = {m.student_id: m for m in session.scalars(select(Match).where(Match.college_id == college, Match.job_id == job.id))}
    now = datetime.now(timezone.utc)
    for student in students:
        calculation = calculate_match(student, *(items[student.id] for items in grouped), job).model_dump()
        row = existing.get(student.id)
        if row is None:
            session.add(Match(college_id=college, job_id=job.id, student_id=student.id, calculated_at=now, **calculation))
        else:
            # Loaded with both tenant and job filters; keep manual decision and audit.
            session.execute(update(Match).where(Match.id == row.id, Match.college_id == college,
                Match.job_id == job.id).values(**calculation, calculated_at=now))
    session.flush()
    return summary(session, job)


def shortlisted(row):
    return row.override_action == "promote" or (row.override_action is None and row.eligible)


def all_matches(session, job):
    return session.scalars(select(Match).where(Match.college_id == job.college_id, Match.job_id == job.id)
        .order_by(Match.match_score.desc(), Match.student_id)).all()


def summary(session, job, rows=None):
    rows = all_matches(session, job) if rows is None else rows
    accepted = sum(shortlisted(m) for m in rows)
    return MatchSummary(job_id=job.id, total=len(rows), shortlisted=accepted, excluded=len(rows)-accepted,
        overridden=sum(m.override_action is not None for m in rows))


def candidate_response(row, student, audit):
    calculation = MatchCalculation.model_validate(row, from_attributes=True)
    return CandidateResponse(**calculation.model_dump(), id=row.id, job_id=row.job_id, student_id=row.student_id,
        student_name=student.name, branch=student.branch, calculated_at=row.calculated_at,
        override_action=row.override_action, shortlist_status="shortlisted" if shortlisted(row) else "excluded",
        audit=[OverrideResponse.model_validate(a, from_attributes=True) for a in audit])


def match_results(session, job, status, offset, limit):
    rows = all_matches(session, job)  # Simple descending sort, no secondary ranking algorithm.
    totals = summary(session, job, rows)
    selected = [m for m in rows if status == "all" or shortlisted(m) == (status == "shortlisted")]
    page = selected[offset:offset+limit]
    ids = [m.student_id for m in page]
    students = {s.id: s for s in session.scalars(select(Student).where(Student.college_id == job.college_id, Student.id.in_(ids)))}
    audit = defaultdict(list)
    for item in session.scalars(select(MatchOverride).where(MatchOverride.college_id == job.college_id,
            MatchOverride.match_id.in_([m.id for m in page])).order_by(MatchOverride.created_at, MatchOverride.id)):
        audit[item.match_id].append(item)
    return MatchResults(**totals.model_dump(), candidates=[candidate_response(m, students[m.student_id], audit[m.id]) for m in page],
        offset=offset, limit=limit)


def override_match(session, user, job, match_id, payload):
    row = session.scalar(select(Match).where(Match.college_id == user.college_id, Match.job_id == job.id, Match.id == match_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Candidate match not found. Run matching first.")
    snapshot = MatchCalculation.model_validate(row, from_attributes=True).model_dump()
    session.add(MatchOverride(college_id=user.college_id, match_id=row.id, recruiter_user_id=user.id,
        action=payload.action, reason=payload.reason, previous_action=row.override_action,
        score_at_action=row.match_score, evidence_at_action=snapshot))
    session.execute(update(Match).where(Match.id == row.id, Match.college_id == user.college_id,
        Match.job_id == job.id).values(override_action=payload.action))
    session.flush()
    student = session.scalar(select(Student).where(Student.id == row.student_id, Student.college_id == user.college_id))
    audit = session.scalars(select(MatchOverride).where(MatchOverride.college_id == user.college_id,
        MatchOverride.match_id == row.id).order_by(MatchOverride.created_at, MatchOverride.id)).all()
    return candidate_response(row, student, audit)
