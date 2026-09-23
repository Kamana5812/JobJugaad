"""Simulated database-backed feed only; never sends email, SMS or external messages."""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert
from models import Notification, Student, User
from schemas import NotificationResponse, NotificationFeed


def notify(session, college, recipient, key, title, body, target, kind="offer"):
    # PostgreSQL conflict handling makes retries idempotent; tenant FK binds recipient.
    session.execute(insert(Notification).values(college_id=college, recipient_user_id=recipient,
        event_key=key, kind=kind, title=title, body=body, target_path=target)
        .on_conflict_do_nothing(index_elements=["college_id","recipient_user_id","event_key"]))


def notify_student(session, college, student_id, key, title, body, kind="interview"):
    student = session.scalar(select(Student).where(Student.college_id == college, Student.id == student_id))
    if student is None:
        raise HTTPException(404, "Student not found.")
    notify(session, college, student.user_id, key, title, body,
        "/student/offers" if kind == "offer" else "/notifications", kind)


def notify_admins(session, college, key, title, body):
    for identity in session.scalars(select(User.id).where(User.college_id == college, User.role == "admin")):
        notify(session, college, identity, key, title, body, "/admin", "offer")


def feed(session, user, offset=0, limit=20):
    scope = (Notification.college_id == user.college_id, Notification.recipient_user_id == user.id)
    total = session.scalar(select(func.count()).select_from(Notification).where(*scope))
    unread = session.scalar(select(func.count()).select_from(Notification).where(*scope, Notification.read_at.is_(None)))
    rows = session.scalars(select(Notification).where(*scope).order_by(Notification.id.desc()).offset(offset).limit(limit)).all()
    return NotificationFeed(notifications=[NotificationResponse.model_validate(row,from_attributes=True) for row in rows],
        total=total,unread_count=unread,offset=offset,limit=limit)


def mark_read(session, user, identity):
    row = session.scalar(select(Notification).where(Notification.college_id == user.college_id,
        Notification.recipient_user_id == user.id, Notification.id == identity).with_for_update())
    if row is None:
        raise HTTPException(404, "Notification not found.")
    if row.read_at is None:
        session.execute(update(Notification).where(Notification.college_id == user.college_id,
            Notification.recipient_user_id == user.id, Notification.id == identity).values(read_at=datetime.now(timezone.utc)))
    return NotificationResponse.model_validate(row,from_attributes=True)
