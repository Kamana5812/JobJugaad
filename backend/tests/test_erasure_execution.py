"""Erasure executes only on disposable loopback fixtures, never live records."""
import os
import unittest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from database import engine, initialize_schema, tenant_session
from models import User, Student, StudentSkill, DataRequest
from operations.erasure import plan, erase

class ErasureExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('ALLOW_TEST_DATABASE') != 'yes' or engine.url.host not in ('localhost', '127.0.0.1'):
            raise RuntimeError('Explicit loopback database required.')
        initialize_schema()

    def setUp(self):
        self.college = 10219
        with tenant_session(self.college) as session:
            user = User(college_id=self.college, email=uuid4().hex + '@erasure-test.invalid',
                password_hash='not-a-login-fixture', role='student', disabled_at=datetime.now(timezone.utc))
            session.add(user); session.flush(); self.identity = user.id
            student = Student(college_id=self.college, user_id=user.id, name='Disposable erasure fixture')
            session.add(student); session.flush()
            session.add(StudentSkill(college_id=self.college, student_id=student.id, skill_name='Python', proficiency=70))
            request = DataRequest(college_id=self.college, user_id=user.id, status='restricted_pending_erasure',
                reason='Disposable synthetic erasure test', retention_until=datetime.now(timezone.utc) - timedelta(days=1))
            session.add(request); session.flush(); self.request_id = request.id

    def approval(self):
        return dict(plan_hash=plan(self.college, self.identity)['plan_hash'], approved_by='Synthetic test owner',
            reason='Disposable local fixture only', backup_disposition='Fixture never in a production backup',
            residual_identity_review='No identity mentions outside fixture records')

    def test_atomic_owned_erasure_and_cross_college_denial(self):
        with self.assertRaises(ValueError):
            plan(10229, self.identity)
        result = erase(self.college, self.identity, self.approval())
        self.assertTrue(result['applied'])
        self.assertFalse(result['backup_erasure_completed'])
        with tenant_session(self.college) as session:
            self.assertIsNone(session.scalar(select(User.id).where(User.college_id == self.college, User.id == self.identity)))

    def test_retention_and_stale_manifest_fail_closed(self):
        approval = self.approval()
        with tenant_session(self.college) as session:
            session.execute(update(DataRequest).where(DataRequest.college_id == self.college,
                DataRequest.id == self.request_id).values(retention_until=datetime.now(timezone.utc) + timedelta(days=2)))
        with self.assertRaises(ValueError):
            erase(self.college, self.identity, approval)
        with self.assertRaises(ValueError):
            erase(self.college, self.identity, {**approval, 'plan_hash': 'invalid'})
        with tenant_session(self.college) as session:
            self.assertEqual(session.scalar(select(User.id).where(User.college_id == self.college, User.id == self.identity)), self.identity)
