"""Tenant-scoped recruiter operations and auditable human shortlist decisions."""
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update, func, or_, and_
from sqlalchemy.dialects.postgresql import insert
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
    now = datetime.now(timezone.utc)
    for offset in range(0,len(students),100):
        values=[dict(college_id=college,job_id=job.id,student_id=student.id,calculated_at=now,
            **calculate_match(student,*(items[student.id] for items in grouped),job).model_dump())
            for student in students[offset:offset+100]]
        statement=insert(Match).values(values)
        # Only computed evidence changes on conflict. Human override and creation time are retained.
        computed=set(values[0]) - {"college_id","job_id","student_id"}
        session.execute(statement.on_conflict_do_update(index_elements=["job_id","student_id","college_id"],
            set_={name:getattr(statement.excluded,name) for name in computed},
            where=and_(Match.college_id==college,Match.job_id==job.id)))
    session.flush()
    return summary(session, job)


def shortlisted(row):
    return row.override_action == "promote" or (row.override_action is None and row.eligible)


def all_matches(session, job):
    return session.scalars(select(Match).where(Match.college_id == job.college_id, Match.job_id == job.id)
        .order_by(Match.match_score.desc(), Match.student_id)).all()


def shortlist_filter():
    return or_(func.coalesce(Match.override_action=="promote",False),and_(Match.override_action.is_(None),Match.eligible.is_(True)))


def summary(session, job, rows=None):
    if rows is not None:
        total=len(rows);accepted=sum(shortlisted(m) for m in rows);overridden=sum(m.override_action is not None for m in rows)
    else:
        scope=(Match.college_id==job.college_id,Match.job_id==job.id)
        total=session.scalar(select(func.count()).select_from(Match).where(*scope))
        accepted=session.scalar(select(func.count()).select_from(Match).where(*scope,shortlist_filter()))
        overridden=session.scalar(select(func.count()).select_from(Match).where(*scope,Match.override_action.is_not(None)))
    return MatchSummary(job_id=job.id,total=total,shortlisted=accepted,excluded=total-accepted,overridden=overridden)


def candidate_response(row, student, audit):
    calculation = MatchCalculation.model_validate(row, from_attributes=True)
    return CandidateResponse(**calculation.model_dump(), id=row.id, job_id=row.job_id, student_id=row.student_id,
        student_name=student.name, branch=student.branch, calculated_at=row.calculated_at,
        override_action=row.override_action, shortlist_status="shortlisted" if shortlisted(row) else "excluded",
        audit=[OverrideResponse.model_validate(a, from_attributes=True) for a in audit])


def match_results(session, job, status, offset, limit):
    totals=summary(session,job)
    query=select(Match).where(Match.college_id==job.college_id,Match.job_id==job.id)
    if status!="all":query=query.where(shortlist_filter() if status=="shortlisted" else ~shortlist_filter())
    # Same descending score and student-ID tie-breaker; pagination happens in PostgreSQL.
    page=session.scalars(query.order_by(Match.match_score.desc(),Match.student_id).offset(offset).limit(limit)).all()
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
