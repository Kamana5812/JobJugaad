"""Manually reviewed, targeted in-app messages; no email, timer, LLM or score."""
import hashlib
import json
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import and_, exists, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import aliased
from models import (User, Student, Company, Job, Application, Match, Interview,
    Notification, DriveAnnouncement, AnnouncementRecipient)
from schemas import (AnnouncementInput, AnnouncementPreviewResponse, AnnouncementSample,
    AnnouncementOptions, NamedOption, AnnouncementResponse, AnnouncementList,
    AnnouncementRecipientResponse, AnnouncementRecipientList)
from engines.accounts import approved_scope

AUDIENCE_EXPLANATIONS = {
    "applicants": "Active submitted, under-review or shortlisted applications; withdrawn and rejected applications are excluded.",
    "shortlisted": "Saved application shortlists or saved effective matching shortlists (promoted or eligible without rejection). A rejected/withdrawn application or rejected matching override vetoes inclusion. Saved matching evidence is not recalculated here.",
    "scheduled": "Confirmed interview records with status scheduled; pending proposals, completed interviews and cancellations are excluded. This is a status-based audience, not necessarily upcoming interviews; unrecorded outcomes can leave past interviews scheduled.",
    "college_students": "All student-role accounts allowed by this college's current access rules, without applying drive eligibility rules. Real-college accounts require inbox verification and college approval; archived demo accounts remain separate.",
}
PUBLISHED_EXPLANATION = ("Published message and recipient identities are frozen. Read counts reflect the notification's marked-read state, not inbox delivery or comprehension. "
    "Messages are recorded in-app only; no email, SMS or automatic reminder timer is used.")
RECIPIENT_EXPLANATION = ("Names and branches are publication-time snapshots. Read timestamps come from the owning student's notification record; "
    "they indicate marked read, not delivery or comprehension. No email or SMS is sent.")


def normalized_branch(value):
    # Same Unicode case/whitespace behavior as AnnouncementInput, including
    # uppercase expansions. PostgreSQL locale-specific upper() can differ.
    return " ".join(value.upper().split())


def drive_query(college):
    recruiter = aliased(User)
    return select(Job, Company).join(Company,
        (Company.id == Job.company_id) & (Company.college_id == Job.college_id)).join(recruiter,
        (recruiter.id == Company.recruiter_user_id) & (recruiter.college_id == Company.college_id)).where(
        Job.college_id == college, Company.college_id == college, recruiter.college_id == college,
        recruiter.role == "recruiter", approved_scope(Company.recruiter_user_id, college, "recruiter"))


def resolve_drive(session, college, job_id):
    result = session.execute(drive_query(college).where(Job.id == job_id)).first()
    if result is None:
        raise HTTPException(404, "Recruiter drive with current account access not found in this college.")
    return result


def students_query(college):
    student_user = aliased(User)
    # User.role must be explicit even in archive colleges: an administrator can
    # retain a Student row after promotion and must not become an audience member.
    return select(Student.id.label("student_id"), Student.user_id.label("user_id"),
        Student.name.label("name"), Student.branch.label("branch")).join(student_user,
        (student_user.id == Student.user_id) & (student_user.college_id == Student.college_id)).where(
        Student.college_id == college, student_user.college_id == college, student_user.role == "student",
        approved_scope(Student.user_id, college, "student"))


def audience_rows(session, college, payload):
    query = students_query(college)
    app_scope = (Application.college_id == college, Application.job_id == payload.job_id,
        Application.student_id == Student.id)
    match_scope = (Match.college_id == college, Match.job_id == payload.job_id, Match.student_id == Student.id)
    if payload.audience == "applicants":
        query = query.where(exists(select(Application.id).where(*app_scope,
            Application.status.in_(["submitted", "under_review", "shortlisted"]))))
    elif payload.audience == "shortlisted":
        app_shortlist = exists(select(Application.id).where(*app_scope, Application.status == "shortlisted"))
        effective_match = exists(select(Match.id).where(*match_scope, or_(Match.override_action == "promote",
            and_(Match.eligible.is_(True), Match.override_action.is_(None)))))
        rejected_app = exists(select(Application.id).where(*app_scope, Application.status.in_(["rejected", "withdrawn"])))
        rejected_override = exists(select(Match.id).where(*match_scope, Match.override_action == "reject"))
        query = query.where(or_(app_shortlist, effective_match), ~rejected_app, ~rejected_override)
    elif payload.audience == "scheduled":
        query = query.where(exists(select(Interview.id).where(Interview.college_id == college,
            Interview.job_id == payload.job_id, Interview.student_id == Student.id, Interview.status == "scheduled")))
    # One statement captures current audience decisions, identities and profile
    # names/branches together. Publication freezes this result; independently
    # changing applications/profiles are not locked or automatically replayed.
    rows = []
    for selected in session.execute(query.order_by(Student.id)).mappings().all():
        row = dict(selected)
        row["branch"] = normalized_branch(row["branch"])
        if payload.branch is None or row["branch"] == payload.branch:
            rows.append(row)
    return rows


def content(payload):
    return payload.model_dump(mode="json", exclude={"preview_hash", "idempotency_key"})


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def capture(session, college, payload):
    job, company = resolve_drive(session, college, payload.job_id)
    rows = audience_rows(session, college, payload)
    preview_hash = digest({"college_id": college, "content": content(payload),
        "drive": {"id": job.id, "title": job.title, "company_id": company.id,
            "company_name": company.name, "recruiter_user_id": company.recruiter_user_id}, "recipients": rows})
    return job, company, rows, preview_hash


def preview(session, user, payload):
    job, company, rows, preview_hash = capture(session, user.college_id, payload)
    explanation = (AUDIENCE_EXPLANATIONS[payload.audience] + " Real-college recipients must be email-verified and college-approved; "
        "archived demo tenants use existing student-role accounts inside their own college. "
        + (f"Branch filter: {payload.branch}. " if payload.branch else "No branch filter. ")
        + "Review the exact message and recipient count before publishing. A changed audience or drive/profile snapshot requires a new preview. No message has been published; in-app only, no email or SMS.")
    return AnnouncementPreviewResponse(**content(payload), job_title=job.title, company_name=company.name,
        recipient_count=len(rows), sample=[AnnouncementSample(student_id=r["student_id"], name=r["name"], branch=r["branch"]) for r in rows[:10]],
        preview_hash=preview_hash, explanation=explanation)


def options(session, user):
    drives = session.execute(drive_query(user.college_id).order_by(Job.id.desc())).all()
    branch_values = session.scalars(students_query(user.college_id).with_only_columns(Student.branch,
        maintain_column_froms=True)).all()
    branches = sorted({normalized_branch(value) for value in branch_values})
    return AnnouncementOptions(jobs=[NamedOption(id=job.id, name=f"{job.title} · {company.name}") for job, company in drives],
        branches=branches, explanation="Recruiter drives and student branches allowed by your college's current account access rules. Real-college accounts require inbox verification and college approval; archived demo accounts remain separate. Preview and manually publish an in-app update or reminder; no email/SMS or background timer.")


def notification_join():
    return and_(Notification.college_id == AnnouncementRecipient.college_id,
        Notification.recipient_user_id == AnnouncementRecipient.recipient_user_id,
        Notification.event_key == AnnouncementRecipient.event_key)


def read_counts(session, college, announcement_ids):
    if not announcement_ids:
        return {}
    return dict(session.execute(select(AnnouncementRecipient.announcement_id, func.count(Notification.id))
        .join(Notification, notification_join()).where(AnnouncementRecipient.college_id == college,
            Notification.college_id == college, AnnouncementRecipient.announcement_id.in_(announcement_ids),
            Notification.read_at.is_not(None)).group_by(AnnouncementRecipient.announcement_id)).all())


def response(row, read_count=0):
    return AnnouncementResponse(id=row.id, job_id=row.job_id, job_title=row.job_title, company_name=row.company_name,
        audience=row.audience, branch=row.branch, kind=row.kind, title=row.title, body=row.body,
        published_by=row.published_by, published_at=row.published_at, recipient_count=row.recipient_count,
        read_count=read_count, explanation=AUDIENCE_EXPLANATIONS[row.audience] + " " + PUBLISHED_EXPLANATION)


def chunks(rows, size=500):
    for offset in range(0, len(rows), size):
        yield rows[offset:offset + size]


def persist_notifications(session, college, announcement, rows):
    # Batched inserts stay in the caller's transaction; no per-recipient query,
    # email adapter call, or independent commit occurs here.
    event_key = f"drive-announcement:{announcement.id}"
    for batch in chunks(rows):
        session.execute(insert(Notification), [dict(college_id=college, recipient_user_id=row["user_id"],
            event_key=event_key, kind=f"drive_{announcement.kind}", title=announcement.title,
            body=f"{announcement.job_title} · {announcement.company_name}\n\n{announcement.body}",
            target_path="/student#applications", created_at=announcement.published_at) for row in batch])


def publish(session, user, payload):
    # Serializes announcement publication/retries for a college. Other workflow
    # writers remain independent; recipient selection is frozen at its query.
    session.execute(text("SELECT pg_advisory_xact_lock(20260402, :college)"), {"college": user.college_id})
    request_hash = digest(content(payload))
    existing = session.scalar(select(DriveAnnouncement).where(DriveAnnouncement.college_id == user.college_id,
        DriveAnnouncement.idempotency_key == str(payload.idempotency_key)))
    if existing is not None:
        if existing.request_hash != request_hash:
            raise HTTPException(409, "This publish key was already used for different content. Preview the new message before publishing.")
        return response(existing, read_counts(session, user.college_id, [existing.id]).get(existing.id, 0))
    job, company, rows, fresh_hash = capture(session, user.college_id, payload)
    if fresh_hash != payload.preview_hash:
        raise HTTPException(409, "The message, drive or recipient audience changed since preview. Refresh the preview and review it before publishing; no message was published.")
    if not rows:
        raise HTTPException(409, "No student accounts match this audience and branch under the current access rules. Choose a different audience; no message was published.")
    announcement = DriveAnnouncement(college_id=user.college_id, company_id=company.id, job_title=job.title,
        company_name=company.name, published_by=user.id, published_at=datetime.now(timezone.utc),
        recipient_count=len(rows), idempotency_key=str(payload.idempotency_key), request_hash=request_hash,
        preview_hash=fresh_hash, **content(payload))
    session.add(announcement)
    session.flush()
    persist_notifications(session, user.college_id, announcement, rows)
    event_key = f"drive-announcement:{announcement.id}"
    for batch in chunks(rows):
        session.execute(insert(AnnouncementRecipient), [dict(college_id=user.college_id, announcement_id=announcement.id,
            student_id=row["student_id"], recipient_user_id=row["user_id"], student_name=row["name"],
            branch=row["branch"], event_key=event_key) for row in batch])
    return response(announcement)


def listing(session, user, offset, limit):
    scope = DriveAnnouncement.college_id == user.college_id
    total = session.scalar(select(func.count()).select_from(DriveAnnouncement).where(scope))
    rows = session.scalars(select(DriveAnnouncement).where(scope)
        .order_by(DriveAnnouncement.id.desc()).offset(offset).limit(limit)).all()
    counts = read_counts(session, user.college_id, [row.id for row in rows])
    return AnnouncementList(items=[response(row, counts.get(row.id, 0)) for row in rows], total=total, offset=offset, limit=limit)


def recipients(session, user, announcement_id, offset, limit):
    announcement = session.scalar(select(DriveAnnouncement).where(DriveAnnouncement.college_id == user.college_id,
        DriveAnnouncement.id == announcement_id))
    if announcement is None:
        raise HTTPException(404, "Announcement not found in this college.")
    rows = session.execute(select(AnnouncementRecipient, Notification.id, Notification.read_at).join(Notification,
        notification_join()).where(AnnouncementRecipient.college_id == user.college_id,
            Notification.college_id == user.college_id, AnnouncementRecipient.announcement_id == announcement_id)
        .order_by(AnnouncementRecipient.student_id).offset(offset).limit(limit)).all()
    return AnnouncementRecipientList(items=[AnnouncementRecipientResponse(student_id=row.student_id,
        name=row.student_name, branch=row.branch, notification_id=notification_id, read_at=read_at)
        for row, notification_id, read_at in rows], total=announcement.recipient_count, offset=offset, limit=limit,
        explanation=RECIPIENT_EXPLANATION)
