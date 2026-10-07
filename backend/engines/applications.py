"""Student consent and human review; immutable weighted-rule evidence, no hiring automation."""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update, func
from models import Application, ApplicationEvent, Student, Job, Company
from schemas import ApplicationResponse, ApplicationEventResponse, ApplicationList
from engines.accounts import approved_scope
from engines.profile import collections
from engines.scoring_evidence import resolve_scoring
from engines.matching import calculate_match
from engines.notifications import notify

ACTIVE = {"submitted", "under_review", "shortlisted"}

def review_profile(session, user, job, application_id):
    """Only authorised reviewers of an active, consenting application see its profile."""
    if user.role not in {"admin", "recruiter"} or job.college_id != user.college_id:
        raise HTTPException(403, "A college reviewer is required.")
    row = session.scalar(select(Application).where(Application.college_id == user.college_id,
        Application.id == application_id, Application.job_id == job.id,
        Application.status.in_(ACTIVE)))
    if row is None:
        raise HTTPException(404, "Active application not found. Closed applications do not grant profile access.")
    student = session.scalar(select(Student).where(Student.college_id == user.college_id,
        Student.id == row.student_id))
    if student is None:
        raise HTTPException(404, "Profile not found.")
    from engines.profile import profile_response
    return profile_response(session, student)
TRANSITIONS = {
    "submitted": {"under_review", "shortlisted", "rejected"},
    "under_review": {"shortlisted", "rejected"},
    "shortlisted": {"under_review", "rejected"},
}


def response(session, row):
    history = session.scalars(select(ApplicationEvent).where(
        ApplicationEvent.college_id == row.college_id,
        ApplicationEvent.application_id == row.id).order_by(ApplicationEvent.id)).all()
    frozen = row.evidence_snapshot
    return ApplicationResponse(id=row.id, student_id=row.student_id,
        student_name=frozen["student_name"], job_id=row.job_id,
        job_title=frozen["job_title"], company_name=frozen["company_name"],
        status=row.status, cover_note=row.cover_note, version=row.version,
        created_at=row.created_at, updated_at=row.updated_at, evidence=frozen["calculation"],
        history=[ApplicationEventResponse.model_validate(e, from_attributes=True) for e in history])


def record_event(session, user, row, previous, reason):
    session.add(ApplicationEvent(college_id=user.college_id, application_id=row.id,
        actor_user_id=user.id, previous_status=previous, status=row.status, reason=reason))
    # Only consenting student's submission goes to the owning recruiter; no external delivery.
    student = session.scalar(select(Student).where(Student.college_id == user.college_id,
        Student.id == row.student_id))
    owner = session.scalar(select(Company.recruiter_user_id).join(Job,
        (Job.company_id == Company.id) & (Job.college_id == Company.college_id)).where(
        Company.college_id == user.college_id, Job.college_id == user.college_id, Job.id == row.job_id))
    for recipient, target in [(student.user_id, "/student#applications"), (owner, "/recruiter#applications")]:
        notify(session, user.college_id, recipient, f"application:{row.id}:{row.version}",
            "Application status updated", f"{row.evidence_snapshot['job_title']}: {row.status.replace('_', ' ')}. {reason}",
            target, "application")
    session.flush()


def submit(session, user, student, payload):
    # Lock the same student row as profile writes; serialize duplicate submissions.
    student = session.scalar(select(Student).where(Student.college_id == user.college_id,
        Student.id == student.id, Student.user_id == user.id).with_for_update().execution_options(populate_existing=True))
    pair = session.execute(select(Job, Company).join(Company,
        (Company.id == Job.company_id) & (Company.college_id == Job.college_id)).where(
        Job.college_id == user.college_id, Company.college_id == user.college_id,
        Job.id == payload.job_id, Job.is_open.is_(True), approved_scope(Company.recruiter_user_id, user.college_id, "recruiter"))
        .with_for_update(of=Job)).first()
    if pair is None:
        raise HTTPException(404, "College drive not found. Historical market references cannot receive applications.")
    job, company = pair
    if session.scalar(select(Application.id).where(Application.college_id == user.college_id,
        Application.student_id == student.id, Application.job_id == job.id)) is not None:
        raise HTTPException(409, "You already applied to this drive. Open the recorded application to view its status.")
    evidence = collections(session, student)
    # Reuse the existing proposed weighted rule, including its unvalidated starting weights.
    scoring_student, scoring_skills = resolve_scoring(session, student, evidence['skills'])
    calculation = calculate_match(scoring_student, scoring_skills, evidence["projects"], evidence["certifications"], job)
    row = Application(college_id=user.college_id, student_id=student.id, job_id=job.id,
        cover_note=payload.cover_note, evidence_snapshot={"calculation": calculation.model_dump(),
            "student_name": student.name, "job_title": job.title, "company_name": company.name})
    session.add(row)
    session.flush()
    # Low scores/gaps remain visible for human review; submission does not alter matches.
    record_event(session, user, row, None, "Student submitted this application for recruiter review.")
    return response(session, row)


def listing(session, college, scope, offset, limit):
    filters = (Application.college_id == college, scope)
    total = session.scalar(select(func.count()).select_from(Application).where(*filters))
    rows = session.scalars(select(Application).where(*filters)
        .order_by(Application.id.desc()).offset(offset).limit(limit)).all()
    return ApplicationList(items=[response(session, row) for row in rows], total=total, offset=offset, limit=limit)


def action(session, user, identity, scope, payload, withdraw=False):
    row = session.scalar(select(Application).where(Application.college_id == user.college_id,
        Application.id == identity, scope).with_for_update())
    if row is None:
        raise HTTPException(404, "Application not found.")
    if row.version != payload.version:
        raise HTTPException(409, "This application changed. Refresh before recording another action.")
    status = "withdrawn" if withdraw else payload.status
    if row.status not in ACTIVE or (not withdraw and status not in TRANSITIONS[row.status]):
        raise HTTPException(409, "This status change is not available. Rejected and withdrawn applications are closed.")
    previous = row.status
    session.execute(update(Application).where(Application.college_id == user.college_id,
        Application.id == row.id, scope, Application.version == payload.version).values(
        status=status, version=row.version + 1, updated_at=datetime.now(timezone.utc)))
    record_event(session, user, row, previous, payload.reason)
    
    if status == "shortlisted":
        # Auto-interview creation pipeline
        from models import Interview
        from datetime import timedelta
        # Schedule it for tomorrow by default
        scheduled = datetime.now(timezone.utc) + timedelta(days=1)
        end = scheduled + timedelta(hours=1)
        interview = Interview(
            college_id=user.college_id,
            job_id=row.job_id,
            student_id=row.student_id,
            scheduled_time=scheduled,
            end_time=end,
            venue="TBD",
            panel_id="Auto-assigned",
            status="scheduled",
            round_name="Auto-Shortlisted Interview"
        )
        session.add(interview)
        session.flush()
        
    return response(session, row)
