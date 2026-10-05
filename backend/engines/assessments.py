"""College-scoped external assessment declarations, never inferred or self-verified."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException
from sqlalchemy import select, func
from models import Assessment, Student
from schemas import AssessmentResponse, AssessmentList


def response(row, name):
    value = float((Decimal(str(row.score)) * 100 / Decimal(str(row.maximum))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP))
    return AssessmentResponse(id=row.id, student_id=row.student_id, student_name=name,
        kind=row.kind, use_for_scoring=row.use_for_scoring, skill_name=row.skill_name, title=row.title, source=row.source,
        reference=row.reference, assessed_on=row.assessed_on.isoformat(), score=row.score,
        maximum=row.maximum, normalized_score=value,
        explanation=f"Recorded {row.score:g} out of {row.maximum:g} for {row.title} from {row.source}; score / maximum × 100 = {value:g}/100. This is a staff declaration, not independently authenticated evidence. " + ('Explicitly adopted for scoring while active; newer adopted results of this type take precedence.' if row.use_for_scoring else 'Evidence only; not adopted for scoring.'),
        recorded_by=row.recorded_by, created_at=row.created_at.isoformat(), reason=row.reason,
        withdrawn_at=row.withdrawn_at.isoformat() if row.withdrawn_at else None,
        withdrawn_by=row.withdrawn_by, withdrawal_reason=row.withdrawal_reason)

def refresh_readiness(session, student):
    from engines.profile import profile_response, update_fields
    update_fields(session, student, {'readiness_score': profile_response(session, student).readiness.score})


def list_records(session, user, student_id=None, offset=0, limit=20):
    filters = [Assessment.college_id == user.college_id]
    if student_id is not None:
        filters.append(Assessment.student_id == student_id)
    total = session.scalar(select(func.count()).select_from(Assessment).where(*filters))
    rows = session.execute(select(Assessment, Student.name).join(Student,
        (Student.id == Assessment.student_id) & (Student.college_id == Assessment.college_id))
        .where(*filters, Student.college_id == user.college_id)
        .order_by(Assessment.id.desc()).offset(offset).limit(limit)).all()
    return AssessmentList(items=[response(row, name) for row, name in rows],
        total=total, offset=offset, limit=limit)


def create(session, user, payload):
    student = session.scalar(select(Student).where(Student.id == payload.student_id,
        Student.college_id == user.college_id))
    if student is None:
        raise HTTPException(404, 'Student profile not found in your college.')
    try:
        assessed = datetime.fromisoformat(payload.assessed_on.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(422, 'Assessment date must be a valid date/time with a timezone.') from None
    if assessed.tzinfo is None or assessed.utcoffset() is None or assessed > datetime.now(timezone.utc):
        raise HTTPException(422, 'Use a timezone-aware assessment date that is not in the future.')
    if payload.score > payload.maximum:
        raise HTTPException(422, 'Score cannot exceed the maximum score.')
    if (payload.kind == 'skill') != (payload.skill_name is not None):
        raise HTTPException(422, 'Specify a skill name only for a skill assessment.')
    row = Assessment(college_id=user.college_id, recorded_by=user.id,
        **{**payload.model_dump(), 'assessed_on': assessed})
    session.add(row); session.flush()
    if row.use_for_scoring:
        refresh_readiness(session, student)
    return response(row, student.name)


def withdraw(session, user, identity, payload):
    row = session.scalar(select(Assessment).where(Assessment.id == identity,
        Assessment.college_id == user.college_id).with_for_update())
    if row is None:
        raise HTTPException(404, 'Assessment record not found.')
    if row.withdrawn_at is not None:
        raise HTTPException(409, 'This record was already withdrawn; its history is preserved.')
    row.withdrawn_at = datetime.now(timezone.utc)
    row.withdrawn_by = user.id
    row.withdrawal_reason = payload.reason
    session.flush()
    if row.use_for_scoring:
        student = session.scalar(select(Student).where(Student.college_id == user.college_id,
            Student.id == row.student_id))
        refresh_readiness(session, student)
    name = session.scalar(select(Student.name).where(Student.id == row.student_id,
        Student.college_id == user.college_id))
    return response(row, name)
