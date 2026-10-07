"""Disposable real-college fixtures; inbox confirmation is simulated, never real delivery."""
import os
import unittest
import uuid
import json
from unittest.mock import patch
from urllib.parse import urlsplit, parse_qs
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from database import engine, initialize_schema, tenant_session
from main import app
from models import User, AccountAccess, RecruiterBinding, RecruiterWorkspace, Company
from auth import issue_token


class RecruiterWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('ALLOW_TEST_DATABASE') != 'yes' or engine.url.host not in ('127.0.0.1', 'localhost'):
            raise RuntimeError('Explicit disposable localhost database required.')
        initialize_schema()
        cls.client = TestClient(app)

    def signup(self, college=10219, email=None, role='recruiter'):
        credentials = dict(email=email or uuid.uuid4().hex+'@workspace-test.invalid',
            password='Local-workspace-tests-2026', college_id=college)
        payload = {**credentials, 'company': {'name': 'Workspace fixture', 'industry': 'Testing'}} if role == 'recruiter' else {**credentials, 'name': 'Student fixture'}
        result = self.client.post('/auth/recruiter/signup' if role == 'recruiter' else '/auth/signup', json=payload)
        self.assertEqual(result.status_code, 201, result.text)
        account = result.json(); account['credentials'] = credentials
        return account

    def headers(self, account):
        return {'Authorization': 'Bearer '+account['access_token']}

    def verify(self, account, approved=True):
        user = account['user']
        with tenant_session(user['college_id']) as session:
            session.add(AccountAccess(college_id=user['college_id'], user_id=user['user_id'],
                email_verified_at=datetime.now(timezone.utc), approval_status='approved' if approved else 'pending'))

    def request(self, account, college=10229):
        return self.client.post('/recruiter/workspaces', headers=self.headers(account), json={
            'college_id': college, 'consent': True, 'affiliation_reference': 'Company-reference-2026', 'context': 'Disposable test request'})

    def approve(self, account, college=10229):
        with tenant_session(account['user']['college_id']) as session:
            link = session.scalar(select(RecruiterWorkspace).where(RecruiterWorkspace.college_id == account['user']['college_id'],
                RecruiterWorkspace.home_user_id == account['user']['user_id'], RecruiterWorkspace.target_college_id == college))
            target_id = link.target_user_id
        with tenant_session(college) as session:
            session.execute(update(AccountAccess).where(AccountAccess.college_id == college, AccountAccess.user_id == target_id)
                .values(approval_status='approved', version=AccountAccess.version+1))
        return target_id

    def switch(self, account, college=10229):
        return self.client.post('/recruiter/workspaces/switch', headers=self.headers(account), json={'college_id': college})

    def test_one_login_independent_approval_switch_home_and_company_isolation(self):
        owner = self.signup(); self.verify(owner)
        result = self.request(owner); self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(result.json()['items'][1]['access_status'], 'pending')
        self.assertEqual(self.switch(owner).status_code, 403)
        self.approve(owner)
        switched = self.switch(owner); self.assertEqual(switched.status_code, 200, switched.text)
        target = switched.json()
        self.assertEqual(target['user']['home_college_id'], 10219)
        self.assertEqual(target['user']['college_id'], 10229)
        self.assertEqual(self.client.get('/auth/me', headers=self.headers(target)).status_code, 200)
        changed = self.client.put('/recruiters/company', headers=self.headers(target), json={'name': 'Target campus profile', 'industry': 'Testing'})
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(self.client.get('/recruiters/company', headers=self.headers(owner)).json()['name'], 'Workspace fixture')
        returned = self.switch(target, 10219); self.assertEqual(returned.status_code, 200, returned.text)
        self.assertEqual(returned.json()['user']['user_id'], owner['user']['user_id'])
        with tenant_session(10219) as session:
            self.assertEqual(session.scalars(select(RecruiterBinding).where(RecruiterBinding.college_id == 10229)).all(), [])
        with engine.connect() as connection:
            self.assertEqual(connection.execute(select(RecruiterWorkspace.id)).all(), [])
            self.assertEqual(connection.execute(select(RecruiterBinding.id)).all(), [])

    def test_student_unverified_unlinked_and_unknown_colleges_are_denied(self):
        student = self.signup(role='student')
        self.assertEqual(self.request(student).status_code, 403)
        owner = self.signup()
        self.assertEqual(self.request(owner).status_code, 403)
        self.verify(owner)
        self.assertEqual(self.switch(owner).status_code, 404)
        self.assertEqual(self.request(owner, 999999).status_code, 422)
        self.assertEqual(self.request(owner, 1).status_code, 422)

    def test_existing_email_account_is_never_adopted_or_changed(self):
        owner = self.signup(); self.verify(owner)
        existing = self.signup(10229, owner['user']['email'])
        self.assertEqual(self.request(owner).status_code, 409)
        self.assertEqual(self.client.post('/auth/login', json=existing['credentials']).status_code, 200)
        self.assertEqual(len(self.client.get('/recruiter/workspaces', headers=self.headers(owner)).json()['items']), 1)

    def test_local_password_and_unbound_token_cannot_bypass_home_authentication(self):
        owner = self.signup(); self.verify(owner); self.assertEqual(self.request(owner).status_code, 201)
        target_id = self.approve(owner)
        with tenant_session(10229) as session:
            local = session.scalar(select(User).where(User.college_id == 10229, User.id == target_id))
            company = session.scalar(select(Company).where(Company.college_id == 10229, Company.recruiter_user_id == target_id))
            local_token = issue_token(local, company=company, session=session).model_dump()
        self.assertEqual(self.client.get('/auth/me', headers=self.headers(local_token)).status_code, 401)
        self.assertEqual(self.client.post('/auth/login', json={**owner['credentials'], 'college_id': 10229}).status_code, 401)

    def test_home_logout_revokes_target_and_target_logout_revokes_home(self):
        for from_target in (False, True):
            owner = self.signup(); self.verify(owner); self.assertEqual(self.request(owner).status_code, 201)
            self.approve(owner); target = self.switch(owner).json()
            logout = self.client.post('/auth/logout', headers=self.headers(target if from_target else owner))
            self.assertEqual(logout.status_code, 200, logout.text)
            for account in (owner, target):
                self.assertEqual(self.client.get('/auth/me', headers=self.headers(account)).status_code, 401)
            self.assertEqual(self.client.post('/auth/login', json=owner['credentials']).status_code, 200)

    def test_college_rejection_blocks_existing_target_workflow_and_disabled_home_revokes_target(self):
        owner = self.signup(); self.verify(owner); self.request(owner); target_id = self.approve(owner)
        target = self.switch(owner).json()
        with tenant_session(10229) as session:
            session.execute(update(AccountAccess).where(AccountAccess.college_id == 10229, AccountAccess.user_id == target_id)
                .values(approval_status='rejected'))
        self.assertEqual(self.client.get('/recruiters/company', headers=self.headers(target)).status_code, 403)
        self.assertEqual(self.switch(owner).status_code, 403)
        self.assertEqual(self.switch(target, 10219).status_code, 200)
        with tenant_session(10219) as session:
            session.execute(update(User).where(User.college_id == 10219, User.id == owner['user']['user_id'])
                .values(disabled_at=datetime.now(timezone.utc)))
        self.assertEqual(self.client.get('/auth/me', headers=self.headers(target)).status_code, 401)

    def test_target_admin_approval_is_audited_and_other_recruiter_cannot_switch(self):
        owner = self.signup(); self.verify(owner); self.assertEqual(self.request(owner).status_code, 201)
        admin = self.signup(10229, role='student'); self.verify(admin)
        with tenant_session(10229) as session:
            session.execute(update(User).where(User.college_id == 10229, User.id == admin['user']['user_id']).values(role='admin'))
        with patch.dict(os.environ, {'ADMIN_ACCOUNTS': json.dumps([{'email': admin['user']['email'], 'college_id': 10229}])}):
            admin_token = self.client.post('/auth/login', json=admin['credentials']).json()
            queue = self.client.get('/admin/accounts', headers=self.headers(admin_token), params={'limit': 50})
            self.assertEqual(queue.status_code, 200, queue.text)
            row = next(r for r in queue.json()['items'] if r['email'] == owner['user']['email'])
            review = self.client.post(f"/admin/accounts/{row['id']}/review", headers=self.headers(admin_token),
                json={'version': row['version'], 'status': 'approved', 'reason': 'Verified disposable company affiliation'})
            self.assertEqual(review.status_code, 200, review.text)
            self.assertTrue(any(e['action'] == 'approved' for e in review.json()['history']))
        self.assertEqual(self.switch(owner).status_code, 200)
        outsider = self.signup(); self.verify(outsider)
        self.assertEqual(self.switch(outsider).status_code, 404)
        self.assertEqual(len(self.client.get('/recruiter/workspaces', headers=self.headers(outsider)).json()['items']), 1)

    def test_home_password_reset_revokes_workspaces_and_target_recovery_does_not_send(self):
        owner = self.signup(); self.verify(owner); self.request(owner); self.approve(owner)
        target = self.switch(owner).json()
        sent = []
        with patch('engines.email_delivery.configured', return_value=True), patch('engines.email_delivery.send_password_reset', side_effect=lambda recipient, link, key: sent.append(link)):
            result = self.client.post('/auth/password-reset-request', json={'email': owner['user']['email'], 'college_id': 10229})
            self.assertEqual(result.status_code, 200, result.text); self.assertEqual(sent, [])
            result = self.client.post('/auth/password-reset-request', json={'email': owner['user']['email'], 'college_id': 10219})
            self.assertEqual(result.status_code, 200, result.text); self.assertEqual(len(sent), 1)
        fragment = parse_qs(urlsplit(sent[0]).fragment)
        reset = self.client.post('/auth/reset-password', json={'college_id': 10219,
            'token': fragment['token'][0], 'password': 'Replacement-workspace-password-2026'})
        self.assertEqual(reset.status_code, 200, reset.text)
        self.assertEqual(self.client.get('/auth/me', headers=self.headers(target)).status_code, 401)
        self.assertEqual(self.client.post('/auth/login', json={**owner['credentials'], 'password': 'Replacement-workspace-password-2026'}).status_code, 200)
