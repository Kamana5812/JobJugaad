"""Persisted, idempotent due-event reminders; in-app only, no delivery guarantee."""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from database import tenant_session
from models import Interview, Student, User
from engines.accounts import approved_scope
from engines.notifications import notify

def generate(session, college, now=None, user_id=None):
    if os.environ.get('MIGRATION_MAINTENANCE') == 'yes':
        return 0
    now = now or datetime.now(timezone.utc)
    query = select(Interview, Student.user_id).join(Student,
        (Student.id == Interview.student_id) & (Student.college_id == Interview.college_id)).join(User,
        (User.id == Student.user_id) & (User.college_id == Student.college_id)).where(
        Interview.college_id == college, Student.college_id == college, User.college_id == college,
        User.role == 'student', User.disabled_at.is_(None), Interview.status == 'scheduled',
        Interview.scheduled_time > now, Interview.scheduled_time <= now + timedelta(hours=24),
        approved_scope(Student.user_id, college, 'student'))
    if user_id is not None:
        query = query.where(Student.user_id == user_id)
    rows = session.execute(query).all()
    for booking, recipient in rows:
        bucket = '1h' if booking.scheduled_time <= now + timedelta(hours=1) else '24h'
        notify(session, college, recipient, f'event:{booking.id}:reminder:{bucket}',
            f'{booking.event_type.capitalize()} reminder',
            f'{booking.round_name} for drive #{booking.job_id} starts at {booking.scheduled_time.isoformat()} '
            f'in {booking.venue}, panel {booking.panel_id}. This is a recorded in-app reminder; confirm the current calendar before attending.',
            '/student#interviews', 'reminder')
    return len(rows)  # Eligible bookings processed, not a claim of new deliveries/read receipts.

def configured_colleges():
    from colleges import COLLEGES
    raw = os.environ.get('REMINDER_COLLEGE_IDS', '[]')
    values = json.loads(raw)
    if not isinstance(values, list) or any(type(value) is not int or value not in COLLEGES for value in values):
        raise ValueError('REMINDER_COLLEGE_IDS must contain registered integer college IDs.')
    return sorted(set(values))

async def worker(stop):
    colleges = configured_colleges()
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=60)
            break
        except asyncio.TimeoutError:
            pass
        if os.environ.get('MIGRATION_MAINTENANCE') == 'yes':
            continue
        for college in colleges:
            if stop.is_set():
                break
            try:
                def run():
                    with tenant_session(college) as session:
                        return generate(session, college)
                await asyncio.to_thread(run)
            except Exception as error:
                # No credentials, records or SQL statements in logs; retry next sweep.
                logging.getLogger('uvicorn.error').warning('In-app reminder sweep failed: %s', type(error).__name__)
