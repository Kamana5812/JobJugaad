"""Persist explained support indicators and human review without concealing evidence."""
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, update, text
from models import Job, Student, StudentSkill, Interview, RiskPrediction, SupportReview
from schemas import SupportCalculation, SupportResponse, SupportReport, AuditEventResponse
from engines.risk import evaluate_support, METHOD


def tenant_job(session, college, job_id):
    job = session.scalar(select(Job).where(Job.college_id == college, Job.id == job_id))
    if job is None:
        raise HTTPException(404, "Target drive not found.")
    return job


def calculation(row):
    return SupportCalculation(score=row.score, support_priority=row.support_priority, flagged=row.flagged,
        assessable=row.assessable, contributing_factors=row.contributing_factors,
        recommendation=row.recommendation, explanation=row.explanation, methodology=METHOD)


def run_support(session, user, job_id):
    college = user.college_id
    # Serialize support recalculations/reviews; distinct from the calendar lock.
    session.execute(text("SELECT pg_advisory_xact_lock(20260302, :college)"), {"college":college})
    job = tenant_job(session, college, job_id)
    now = datetime.now(timezone.utc)
    students = session.scalars(select(Student).where(Student.college_id == college)).all()
    skills = defaultdict(list)
    for skill in session.scalars(select(StudentSkill).where(StudentSkill.college_id == college)):
        skills[skill.student_id].append(skill)
    attendance = defaultdict(int)
    for booking in session.scalars(select(Interview).where(Interview.college_id == college,
            Interview.status.in_(["completed","selected","rejected"]), Interview.end_time >= now-timedelta(days=30),
            Interview.end_time <= now)):
        attendance[booking.student_id] += 1
    rows = {r.student_id:r for r in session.scalars(select(RiskPrediction).where(RiskPrediction.college_id == college, RiskPrediction.job_id == job_id))}
    for student in students:
        result = evaluate_support(student, skills[student.id], job, attendance[student.id])
        data = result.model_dump(exclude={"methodology","score_label"})
        digest = hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
        row = rows.get(student.id)
        if row is None:
            session.add(RiskPrediction(college_id=college, student_id=student.id, job_id=job_id,
                **data, evidence_hash=digest, evaluated_at=now, review_status="active"))
        else:
            session.execute(update(RiskPrediction).where(RiskPrediction.college_id == college, RiskPrediction.id == row.id,
                RiskPrediction.job_id == job_id).values(**data, evidence_hash=digest, evaluated_at=now,
                review_status=row.review_status if row.evidence_hash == digest else "active"))
    session.flush()
    return report(session, user, job_id)


def report(session, user, job_id):
    college = user.college_id
    tenant_job(session, college, job_id)
    rows = session.scalars(select(RiskPrediction).where(RiskPrediction.college_id == college,
        RiskPrediction.job_id == job_id).order_by(RiskPrediction.student_id)).all()
    flagged = [r for r in rows if r.flagged]
    student_ids = [r.student_id for r in flagged]
    students = {s.id:s for s in session.scalars(select(Student).where(Student.college_id == college, Student.id.in_(student_ids)))}
    audits = defaultdict(list)
    for audit in session.scalars(select(SupportReview).where(SupportReview.college_id == college,
            SupportReview.prediction_id.in_([r.id for r in flagged])).order_by(SupportReview.id)):
        audits[audit.prediction_id].append(AuditEventResponse.model_validate(audit,from_attributes=True))
    return SupportReport(job_id=job_id, total_evaluated=len(rows), flagged_count=len(flagged),
        active_count=sum(r.review_status == "active" for r in flagged),
        unknown_interview_score_count=sum(not r.assessable for r in rows), methodology=METHOD,
        students=[SupportResponse(**calculation(r).model_dump(), id=r.id, job_id=r.job_id,
            student_id=r.student_id, student_name=students[r.student_id].name,
            review_status=r.review_status, evaluated_at=r.evaluated_at, audit=audits[r.id]) for r in flagged])


def review_support(session, user, prediction_id, payload):
    session.execute(text("SELECT pg_advisory_xact_lock(20260302, :college)"), {"college":user.college_id})
    row = session.scalar(select(RiskPrediction).where(RiskPrediction.college_id == user.college_id, RiskPrediction.id == prediction_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Support indicator not found.")
    snapshot = calculation(row).model_dump(mode="json")
    snapshot["previous_review_status"] = row.review_status
    session.add(SupportReview(college_id=user.college_id, prediction_id=row.id, actor_user_id=user.id,
        action=payload.action, reason=payload.reason, snapshot=snapshot))
    session.execute(update(RiskPrediction).where(RiskPrediction.college_id == user.college_id, RiskPrediction.id == row.id)
        .values(review_status=payload.action))
    session.flush()
    return report(session, user, row.job_id)
