"""External assessment workflow against isolated PostgreSQL; no real exam claims."""
import json
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from auth import hash_password, issue_token
from database import engine, initialize_schema, tenant_session, isolation_report
from main import app
from models import User, Student, AccountAccess, Assessment


class AssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (os.environ.get('ALLOW_TEST_DATABASE') != 'yes' or engine is None
            or engine.url.host not in ('localhost', '127.0.0.1')
            or engine.url.database not in ('jobjugaad_test', 'jobjugaad_test_utf8')):
            raise RuntimeError('Explicit isolated local test database required.')
        initialize_schema()
        cls.client = TestClient(app)
        cls.accounts = []
        password = hash_password('Local-assessment-tests-2026')
        for college in (10271, 10229):
            account = {'college': college}
            with tenant_session(college) as session:
                for role in ('admin', 'student', 'recruiter'):
                    user = User(college_id=college, email=f'assessment-{uuid.uuid4().hex}@test.invalid',
                        role=role, password_hash=password)
                    session.add(user); session.flush()
                    session.add(AccountAccess(college_id=college, user_id=user.id,
                        email_verified_at=datetime.now(timezone.utc), approval_status='approved'))
                    student = None
                    if role == 'student':
                        student = Student(college_id=college, user_id=user.id, name='Controlled assessment student',
                            branch='CSE', aptitude_score=25)
                        session.add(student); session.flush()
                        account['student_id'] = student.id
                    account[role] = {'email': user.email, 'id': user.id, 'headers': {
                        'Authorization': 'Bearer ' + issue_token(user, student=student, session=session).access_token}}
            cls.accounts.append(account)
        cls.allowlist = patch.dict(os.environ, {'ADMIN_ACCOUNTS': json.dumps([
            {'email': a['admin']['email'], 'college_id': a['college']} for a in cls.accounts])})
        cls.allowlist.start()

    @classmethod
    def tearDownClass(cls):
        cls.allowlist.stop()

    def setUp(self):
        self.a, self.b = self.accounts
        self.payload = dict(student_id=self.a['student_id'], kind='aptitude', title='Controlled practice result',
            source='Controlled local test provider', reference=uuid.uuid4().hex,
            assessed_on=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            score=30, maximum=40, reason='Reviewed a controlled test result, not a real exam.')

    def create(self, payload=None):
        return self.client.post('/admin/assessments', headers=self.a['admin']['headers'], json=payload or self.payload)

    def test_adopted_results_normalize_precedence_and_withdrawal(self):
        path = f"/students/{self.a['student_id']}"
        headers = self.a['student']['headers']
        baseline = self.client.get(path, headers=headers).json()
        first = self.create({**self.payload, 'use_for_scoring': True})
        self.assertEqual(first.status_code, 201, first.text)
        adopted = self.client.get(path, headers=headers).json()
        self.assertEqual(adopted['aptitude_score'], 25)  # Original self-report is preserved.
        factor = next(f for f in adopted['readiness']['breakdown'] if f['key'] == 'aptitude')
        self.assertEqual(factor['value'], 75)
        self.assertIn(f"assessment #{first.json()['id']}", factor['evidence'])
        second = self.create({**self.payload, 'use_for_scoring': True, 'score': 40,
            'assessed_on': datetime.now(timezone.utc).isoformat()})
        self.assertEqual(second.status_code, 201, second.text)
        current = self.client.get(path, headers=headers).json()
        self.assertEqual(next(f for f in current['readiness']['breakdown'] if f['key'] == 'aptitude')['value'], 100)
        for row, expected in ((second.json(), 75), (first.json(), 25)):
            withdrawn = self.client.post(f"/admin/assessments/{row['id']}/withdraw",
                headers=self.a['admin']['headers'], json={'reason': 'Withdraw controlled adopted scoring fixture'})
            self.assertEqual(withdrawn.status_code, 200, withdrawn.text)
            current = self.client.get(path, headers=headers).json()
            self.assertEqual(next(f for f in current['readiness']['breakdown'] if f['key'] == 'aptitude')['value'], expected)
        self.assertEqual(current['readiness'], baseline['readiness'])

    def test_result_provenance_and_no_silent_profile_overwrite(self):
        before = self.client.get(f"/students/{self.a['student_id']}", headers=self.a['student']['headers']).json()
        result = self.create()
        self.assertEqual(result.status_code, 201, result.text)
        data = result.json()
        self.assertEqual(data['normalized_score'], 75)
        self.assertIn('score / maximum', data['explanation'])
        self.assertEqual(data['recorded_by'], self.a['admin']['id'])
        own = self.client.get(f"/students/{self.a['student_id']}/assessments", headers=self.a['student']['headers']).json()
        self.assertIn(data['id'], [row['id'] for row in own['items']])
        after = self.client.get(f"/students/{self.a['student_id']}", headers=self.a['student']['headers']).json()
        self.assertEqual(before, after)

    def test_withdrawal_preserves_result_and_rejects_second_write(self):
        data = self.create().json()
        path = f"/admin/assessments/{data['id']}/withdraw"
        result = self.client.post(path, headers=self.a['admin']['headers'], json={'reason': 'Wrong result reference; withdraw without deleting history.'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['score'], 30)
        self.assertEqual(result.json()['withdrawn_by'], self.a['admin']['id'])
        self.assertEqual(self.client.post(path, headers=self.a['admin']['headers'], json={'reason': 'Attempt second withdrawal.'}).status_code, 409)

    def test_role_and_ownership_boundaries(self):
        for role in ('student', 'recruiter'):
            self.assertEqual(self.client.post('/admin/assessments', headers=self.a[role]['headers'], json=self.payload).status_code, 403)
            self.assertEqual(self.client.get('/admin/assessments', headers=self.a[role]['headers']).status_code, 403)
        self.assertEqual(self.client.get('/admin/assessments').status_code, 401)
        self.assertEqual(self.client.get(f"/students/{self.b['student_id']}/assessments", headers=self.a['student']['headers']).status_code, 404)

    def test_cross_college_application_and_actual_rls(self):
        data = self.create().json()
        self.assertEqual(self.create({**self.payload, 'student_id': self.b['student_id']}).status_code, 404)
        result = self.client.get('/admin/assessments', headers=self.b['admin']['headers']).json()
        self.assertNotIn(data['id'], [row['id'] for row in result['items']])
        with tenant_session(self.b['college']) as session:
            # Intentionally unscoped adversarial read proves the second enforcement layer.
            self.assertIsNone(session.scalar(select(Assessment).where(Assessment.id == data['id'])))
            changed = session.execute(text('UPDATE assessments SET reason = :reason WHERE id = :id'),
                {'reason': 'Adversarial cross-tenant write', 'id': data['id']})
            self.assertEqual(changed.rowcount, 0)
        policy = next(row for row in isolation_report()['tables'] if row['table'] == 'assessments')
        self.assertEqual(policy['status'], 'verified')

    def test_invalid_scale_skill_date_and_forged_actor(self):
        variants = [{'score': 41}, {'maximum': 0}, {'score': -1}, {'kind': 'skill'},
            {'skill_name': 'Python'}, {'assessed_on': 'not-a-date'}, {'assessed_on': '2020-01-01T10:00:00'},
            {'assessed_on': '2099-01-01T10:00:00Z'}, {'recorded_by': self.a['student']['id']}, {'college_id': self.b['college']}]
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertEqual(self.create({**self.payload, **variant}).status_code, 422)

    def test_skill_evidence_and_pagination(self):
        result = self.create({**self.payload, 'kind': 'skill', 'skill_name': 'Python'})
        self.assertEqual(result.status_code, 201, result.text)
        rows = self.client.get('/admin/assessments?limit=1', headers=self.a['admin']['headers']).json()
        self.assertEqual(len(rows['items']), 1)
        self.assertEqual(rows['items'][0]['skill_name'], 'Python')
        self.assertEqual(self.client.get('/admin/assessments?limit=51', headers=self.a['admin']['headers']).status_code, 422)
