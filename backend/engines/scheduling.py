"""Tenant-scoped scheduling workflow and immutable API audit events."""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, update, text
from models import Job, Student, Schedule, Interview, ScheduleEvent
from schemas import ScheduleInput, ScheduleResponse, InterviewResponse, AuditEventResponse, SchedulingBoard, NamedOption, BookingConflict
from engines.scheduler import propose_slot, conflicts_for


def lock_calendar(session, college):
    # PostgreSQL transaction advisory lock serializes all booking writers for a college.
    session.execute(text("SELECT pg_advisory_xact_lock(20260301, :college)"), {"college": college})


def all_bookings(session, college):
    return session.scalars(select(Interview).where(Interview.college_id == college).order_by(Interview.scheduled_time, Interview.id)).all()


def owned_interview(session, college, interview_id):
    row = session.scalar(select(Interview).where(Interview.id == interview_id, Interview.college_id == college))
    if row is None:
        raise HTTPException(404, "Interview not found.")
    return row


def validate_references(session, college, payload):
    if session.scalar(select(Job.id).where(Job.id == payload.job_id, Job.college_id == college)) is None:
        raise HTTPException(404, "Drive not found.")
    if session.scalar(select(Student.id).where(Student.id == payload.student_id, Student.college_id == college)) is None:
        raise HTTPException(404, "Student not found.")
    if payload.reschedule_interview_id:
        source = owned_interview(session, college, payload.reschedule_interview_id)
        if source.status != "scheduled" or (source.student_id, source.job_id) != (payload.student_id, payload.job_id):
            raise HTTPException(409, "Only a scheduled interview for the same student and drive can be rescheduled.")


def check_schedule(session, user, payload):
    validate_references(session, user.college_id, payload)
    if payload.scheduled_time <= datetime.now(timezone.utc):
        raise HTTPException(422, "Choose a future interview time.")
    return propose_slot(payload, all_bookings(session, user.college_id))


def event(session, user, action, reason, snapshot, schedule_id=None, interview_id=None):
    session.add(ScheduleEvent(college_id=user.college_id, actor_user_id=user.id, action=action,
        reason=reason, snapshot=snapshot, schedule_id=schedule_id, interview_id=interview_id))


def response(row):
    return ScheduleResponse.model_validate(row, from_attributes=True)


def create_proposal(session, user, payload):
    lock_calendar(session, user.college_id)
    proposal = check_schedule(session, user, payload)
    if proposal.proposed_time is None:
        raise HTTPException(409, proposal.explanation)
    row = Schedule(college_id=user.college_id, job_id=payload.job_id, student_id=payload.student_id,
        requested_time=payload.scheduled_time, scheduled_time=proposal.proposed_time, end_time=proposal.proposed_end_time,
        venue=payload.venue, panel_id=payload.panel_id, status="pending",
        conflicts=[c.model_dump(mode="json") for c in proposal.conflicts], explanation=proposal.explanation,
        reschedule_interview_id=payload.reschedule_interview_id, created_by=user.id)
    session.add(row)
    session.flush()
    event(session, user, "proposed", "Pending administrator approval.", response(row).model_dump(mode="json"), schedule_id=row.id)
    return response(row)


def pending_schedule(session, user, schedule_id, version):
    row = session.scalar(select(Schedule).where(Schedule.id == schedule_id, Schedule.college_id == user.college_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Schedule proposal not found.")
    if row.status != "pending" or row.version != version:
        raise HTTPException(409, "This proposal changed or was already reviewed. Refresh the calendar.")
    return row


def as_input(row, requested=False):
    return ScheduleInput(job_id=row.job_id, student_id=row.student_id,
        scheduled_time=row.requested_time if requested else row.scheduled_time,
        duration_minutes=int((row.end_time - row.scheduled_time).total_seconds() / 60),
        venue=row.venue, panel_id=row.panel_id, reschedule_interview_id=row.reschedule_interview_id)


def recheck_proposal(session, user, schedule_id, payload):
    lock_calendar(session, user.college_id)
    row = pending_schedule(session, user, schedule_id, payload.version)
    request = as_input(row, requested=True)
    if request.scheduled_time <= datetime.now(timezone.utc):
        request.scheduled_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(minutes=1)
    proposal = check_schedule(session, user, request)
    if proposal.proposed_time is None:
        raise HTTPException(409, proposal.explanation)
    session.execute(update(Schedule).where(Schedule.id == row.id, Schedule.college_id == user.college_id).values(
        scheduled_time=proposal.proposed_time, end_time=proposal.proposed_end_time, version=row.version+1,
        conflicts=[c.model_dump(mode="json") for c in proposal.conflicts], explanation=proposal.explanation))
    event(session, user, "reproposed", "Availability rechecked; new approval required.", response(row).model_dump(mode="json"), schedule_id=row.id)
    return response(row)


def review_proposal(session, user, schedule_id, payload):
    lock_calendar(session, user.college_id)
    row = pending_schedule(session, user, schedule_id, payload.version)
    before = response(row).model_dump(mode="json")
    interview = None
    if payload.action == "approve":
        request = as_input(row)
        validate_references(session, user.college_id, request)
        if request.scheduled_time <= datetime.now(timezone.utc):
            raise HTTPException(409, "This proposed time has passed. Recheck the proposal before approval.")
        if conflicts_for(request, all_bookings(session, user.college_id)):
            raise HTTPException(409, "The proposed slot is now occupied. Recheck for a new proposal; no booking was changed.")
        if row.reschedule_interview_id:
            session.execute(update(Interview).where(Interview.id == row.reschedule_interview_id,
                Interview.college_id == user.college_id).values(status="cancelled"))
        interview = Interview(college_id=user.college_id, schedule_id=row.id, job_id=row.job_id,
            student_id=row.student_id, scheduled_time=row.scheduled_time, end_time=row.end_time,
            venue=row.venue, panel_id=row.panel_id, status="scheduled")
        session.add(interview)
        session.flush()
    session.execute(update(Schedule).where(Schedule.id == row.id, Schedule.college_id == user.college_id).values(
        status="scheduled" if payload.action == "approve" else "rejected",
        reviewed_by=user.id, review_reason=payload.reason, version=row.version+1))
    event(session, user, payload.action, payload.reason, {"before":before,"after":response(row).model_dump(mode="json")},
        schedule_id=row.id, interview_id=interview.id if interview else None)
    return response(row)


def change_interview_status(session, user, interview_id, payload):
    lock_calendar(session, user.college_id)
    row = owned_interview(session, user.college_id, interview_id)
    if row.status == "cancelled":
        raise HTTPException(409, "A cancelled interview cannot be reopened; create a new proposal.")
    if payload.status != "cancelled" and row.end_time > datetime.now(timezone.utc):
        raise HTTPException(422, "Record an interview outcome only after its scheduled end.")
    before = InterviewResponse.model_validate(row, from_attributes=True).model_dump(mode="json")
    session.execute(update(Interview).where(Interview.id == row.id, Interview.college_id == user.college_id).values(status=payload.status))
    result = InterviewResponse.model_validate(row, from_attributes=True)
    event(session, user, "interview_status", payload.reason, {"before":before,"after":result.model_dump(mode="json")}, interview_id=row.id)
    return result


def calendar_board(session, user):
    college = user.college_id
    bookings = all_bookings(session, college)
    conflicts = []
    seen = set()
    for booking in bookings:
        if booking.status == "cancelled":
            continue
        request = ScheduleInput(job_id=booking.job_id, student_id=booking.student_id, scheduled_time=booking.scheduled_time,
            duration_minutes=int((booking.end_time-booking.scheduled_time).total_seconds()/60),
            venue=booking.venue, panel_id=booking.panel_id, reschedule_interview_id=booking.id)
        for conflict in conflicts_for(request, bookings):
            pair = tuple(sorted((booking.id, conflict.interview_id)))
            if pair not in seen:
                seen.add(pair)
                conflicts.append(BookingConflict(interview_id=booking.id, other_interview_id=conflict.interview_id,
                    kinds=conflict.kinds, explanation=f"Interview #{booking.id}: " + conflict.explanation))
    jobs = session.scalars(select(Job).where(Job.college_id == college).order_by(Job.id.desc())).all()
    students = session.scalars(select(Student).where(Student.college_id == college).order_by(Student.name, Student.id)).all()
    proposals = session.scalars(select(Schedule).where(Schedule.college_id == college).order_by(Schedule.id.desc())).all()
    audit = session.scalars(select(ScheduleEvent).where(ScheduleEvent.college_id == college).order_by(ScheduleEvent.id.desc()).limit(50)).all()
    return SchedulingBoard(jobs=[NamedOption(id=j.id,name=j.title) for j in jobs],
        students=[NamedOption(id=s.id,name=s.name) for s in students],
        interviews=[InterviewResponse.model_validate(b,from_attributes=True) for b in bookings],
        proposals=[response(p) for p in proposals], conflicts=conflicts,
        audit=[AuditEventResponse.model_validate(a,from_attributes=True) for a in audit])
