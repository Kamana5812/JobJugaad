"""Tenant-filtered, versioned calendar declarations under the booking lock."""
from datetime import timezone
from fastapi import HTTPException
from sqlalchemy import func, select, update
from models import CalendarSettings, CalendarConstraint, Student
from schemas import (CalendarSettingsResponse, CalendarConstraintResponse,
    CalendarConstraintList, CalendarConstraintInput)


def settings_for(session, college):
    row = session.scalar(select(CalendarSettings).where(CalendarSettings.college_id == college))
    return (CalendarSettingsResponse.model_validate(row, from_attributes=True) if row is not None
        else CalendarSettingsResponse(college_id=college))


def active_constraints(session, college):
    # Include all active dates: existing positive windows must not silently stop
    # applying when a request falls outside the dates the owner supplied.
    return session.scalars(select(CalendarConstraint).where(CalendarConstraint.college_id == college,
        CalendarConstraint.status == "active").order_by(CalendarConstraint.starts_at, CalendarConstraint.id)).all()


def save_settings(session, user, payload):
    from engines.scheduling import lock_calendar, event
    lock_calendar(session, user.college_id)
    row = session.scalar(select(CalendarSettings).where(CalendarSettings.college_id == user.college_id).with_for_update())
    current = row.version if row is not None else 0
    if current != payload.version:
        raise HTTPException(409, "Calendar settings changed. Refresh before saving.")
    before = settings_for(session, user.college_id).model_dump(mode="json")
    values = payload.model_dump(exclude={"version", "reason"})
    if row is None:
        row = CalendarSettings(college_id=user.college_id, version=1, **values)
        session.add(row)
    else:
        session.execute(update(CalendarSettings).where(CalendarSettings.id == row.id,
            CalendarSettings.college_id == user.college_id).values(version=current + 1, **values))
    session.flush()
    after = CalendarSettingsResponse.model_validate(row, from_attributes=True)
    event(session, user, "calendar_settings", payload.reason,
        {"before": before, "after": after.model_dump(mode="json")})
    return after


def constraints_list(session, college, offset, limit, student_id=None):
    conditions = [CalendarConstraint.college_id == college]
    if student_id is not None:
        conditions += [CalendarConstraint.scope == "student", CalendarConstraint.student_id == student_id]
    total = session.scalar(select(func.count()).select_from(CalendarConstraint).where(*conditions))
    rows = session.scalars(select(CalendarConstraint).where(*conditions)
        .order_by(CalendarConstraint.starts_at.desc(), CalendarConstraint.id.desc()).offset(offset).limit(limit)).all()
    return CalendarConstraintList(items=[CalendarConstraintResponse.model_validate(row, from_attributes=True) for row in rows],
        total=total, offset=offset, limit=limit)


def create_constraint(session, user, payload):
    from engines.scheduling import lock_calendar, event
    lock_calendar(session, user.college_id)
    if payload.scope == "student":
        exists = session.scalar(select(Student.id).where(Student.id == payload.student_id, Student.college_id == user.college_id))
        if exists is None:
            raise HTTPException(404, "Student not found in this college.")
    row = CalendarConstraint(college_id=user.college_id, created_by=user.id,
        **payload.model_dump(exclude={"reason", "starts_at", "ends_at"}),
        starts_at=payload.starts_at.astimezone(timezone.utc), ends_at=payload.ends_at.astimezone(timezone.utc))
    session.add(row)
    session.flush()
    result = CalendarConstraintResponse.model_validate(row, from_attributes=True)
    event(session, user, "calendar_constraint_added", payload.reason, {"after": result.model_dump(mode="json")})
    return result


def create_student_availability(session, user, student, payload):
    # Ownership is already checked by the router; scope cannot be supplied by a
    # student. The immutable audit records their actual declarative statement.
    values = payload.model_dump()
    request = CalendarConstraintInput(**values, scope="student", student_id=student.id,
        reason="Student declared own availability: " + payload.label)
    return create_constraint(session, user, request)


def cancel_constraint(session, user, constraint_id, payload, student_id=None):
    from engines.scheduling import lock_calendar, event
    lock_calendar(session, user.college_id)
    conditions = [CalendarConstraint.id == constraint_id, CalendarConstraint.college_id == user.college_id]
    if student_id is not None:
        conditions += [CalendarConstraint.scope == "student", CalendarConstraint.student_id == student_id]
    row = session.scalar(select(CalendarConstraint).where(*conditions).with_for_update())
    if row is None:
        raise HTTPException(404, "Calendar declaration not found.")
    if row.status != "active" or row.version != payload.version:
        raise HTTPException(409, "This declaration changed or was cancelled. Refresh before continuing.")
    before = CalendarConstraintResponse.model_validate(row, from_attributes=True).model_dump(mode="json")
    session.execute(update(CalendarConstraint).where(*conditions).values(status="cancelled", version=row.version + 1))
    result = CalendarConstraintResponse.model_validate(row, from_attributes=True)
    event(session, user, "calendar_constraint_cancelled", payload.reason,
        {"before": before, "after": result.model_dump(mode="json")})
    return result
