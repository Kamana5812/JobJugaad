"""Durable in-app reminders, role/tenant scope and maintenance; local fixtures only."""
import os
import unittest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from sqlalchemy import select
from database import engine, initialize_schema, tenant_session
from models import User, Student, Interview, Job, Company, Notification, AccountAccess
from engines.reminders import generate

class ReminderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('ALLOW_TEST_DATABASE') != 'yes' or engine.url.host not in ('127.0.0.1', 'localhost'):
            raise RuntimeError('Explicit localhost database required.')
        initialize_schema()

    def test_due_buckets_persist_once_cancel_and_maintenance_skip(self):
        college = 10219
        now = datetime.now(timezone.utc)
        with tenant_session(college) as session:
            student_user = User(college_id=college, email=uuid4().hex+'@reminder-test.invalid', role='student', password_hash='not-a-login')
            recruiter = User(college_id=college, email=uuid4().hex+'@reminder-test.invalid', role='recruiter', password_hash='not-a-login')
            session.add_all([student_user, recruiter]); session.flush()
            session.add(AccountAccess(college_id=college, user_id=student_user.id,
                email_verified_at=now, approval_status='approved'))
            student = Student(college_id=college, user_id=student_user.id, name='Controlled reminder fixture')
            company = Company(college_id=college, recruiter_user_id=recruiter.id, name='Controlled reminder company', industry='Testing')
            session.add_all([student, company]); session.flush()
            job = Job(college_id=college, company_id=company.id, title='Controlled reminder role', ctc=6,
                min_cgpa=0, eligible_branches=['CSE'], required_skills=[dict(skill_name='python', min_proficiency=60)],
                weights=dict(skills=40,projects=20,academics=20,assessments=15,certifications=5))
            session.add(job); session.flush()
            booking = Interview(college_id=college, student_id=student.id, job_id=job.id,
                scheduled_time=now+timedelta(hours=2), end_time=now+timedelta(hours=2,minutes=30),
                venue='Controlled room', panel_id='Controlled panel', status='scheduled', event_type='assessment')
            session.add(booking); session.flush()
            identity, recipient = booking.id, student_user.id
            self.assertEqual(generate(session, college, now, recipient), 1)
            generate(session, college, now, recipient)
            def notifications():
                return list(session.scalars(select(Notification).where(Notification.college_id == college,
                    Notification.recipient_user_id == recipient, Notification.kind == 'reminder')))
            self.assertEqual(len(notifications()), 1)
            self.assertTrue(notifications()[0].event_key.endswith(':24h'))
            generate(session, college, now+timedelta(hours=1,minutes=30), recipient)
            generate(session, college, now+timedelta(hours=1,minutes=30), recipient)
            self.assertEqual(len(notifications()), 2)
            booking.status = 'cancelled'; session.flush()
            self.assertEqual(generate(session, college, now, recipient), 0)
            with patch.dict(os.environ, {'MIGRATION_MAINTENANCE': 'yes'}):
                self.assertEqual(generate(session, college, now, recipient), 0)
        with tenant_session(10229) as session:
            self.assertEqual(generate(session, 10229, now, recipient), 0)
            self.assertIsNone(session.scalar(select(Notification.id).where(Notification.college_id == 10229,
                Notification.recipient_user_id == recipient)))
