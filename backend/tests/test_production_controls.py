"""Disposable loopback security/privacy fixtures; no production credentials or mail."""
import json
import os
import unittest
import uuid
from unittest.mock import patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from database import engine, initialize_schema, tenant_session
from models import User, AccountAccess, AuthLimit, DataRequest
from main import app

class ProductionControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('ALLOW_TEST_DATABASE')!='yes' or engine.url.host not in ('127.0.0.1','localhost'):
            raise RuntimeError('Explicit localhost database required.')
        initialize_schema();cls.client=TestClient(app)

    def signup(self,college=10219,role='student'):
        credentials={'email':uuid.uuid4().hex+'@controls-test.invalid','college_id':college,'password':'Local-controls-tests-2026'}
        body={**credentials,'name':'Local privacy fixture'} if role=='student' else {**credentials,'company':{'name':'Local privacy company','industry':'Testing'}}
        result=self.client.post('/auth/signup' if role=='student' else '/auth/recruiter/signup',json=body)
        self.assertEqual(result.status_code,201,result.text)
        data=result.json();data['credentials']=credentials
        return data

    def headers(self,account): return {'Authorization':'Bearer '+account['access_token']}

    def setUp(self):
        self.owner=self.signup();self.other=self.signup();self.admin=self.signup()
        with tenant_session(10219) as session:
            session.execute(update(User).where(User.college_id==10219,User.id==self.admin['user']['user_id']).values(role='admin'))
            session.add(AccountAccess(college_id=10219,user_id=self.admin['user']['user_id'],email_verified_at=datetime.now(timezone.utc)))
        self.allowlist=patch.dict(os.environ,{'ADMIN_ACCOUNTS':json.dumps([{'email':self.admin['user']['email'],'college_id':10219}])})
        self.allowlist.start();self.addCleanup(self.allowlist.stop)
        self.admin=self.client.post('/auth/login',json=self.admin['credentials']).json()

    def test_logout_revokes_every_prior_session_and_allows_new_login(self):
        second=self.client.post('/auth/login',json=self.owner['credentials']).json()
        result=self.client.post('/auth/logout',headers=self.headers(self.owner))
        self.assertEqual(result.status_code,200,result.text)
        for account in (self.owner,second): self.assertEqual(self.client.get('/auth/me',headers=self.headers(account)).status_code,401)
        self.assertEqual(self.client.post('/auth/login',json=self.owner['credentials']).status_code,200)

    def test_owned_export_excludes_other_accounts_and_authentication_secrets(self):
        result=self.client.get('/account/export',headers=self.headers(self.owner))
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['account']['email'],self.owner['user']['email'])
        self.assertNotIn(self.other['user']['email'],result.text)
        for forbidden in ('password_hash','token_hash','request_key','access_token'):
            self.assertNotIn(forbidden,result.text)
        ids=[r['id'] for r in result.json()['records']['students']]
        self.assertEqual(ids,[self.owner['user']['student_id']])
        recruiter=self.signup(role='recruiter')
        data=self.client.get('/account/export',headers=self.headers(recruiter)).json()
        self.assertNotIn('matches',data['records'])

    def request(self):
        result=self.client.post('/account/data-requests',headers=self.headers(self.owner),json={'reason':'Disposable request for testing','confirmation':'REQUEST DELETION'})
        self.assertEqual(result.status_code,201,result.text);return result.json()

    def test_request_review_restricts_access_but_does_not_claim_erasure(self):
        row=self.request()
        payload={'action':'restrict','reason':'Close test access pending retained-record review'}
        self.assertEqual(self.client.post(f"/admin/data-requests/{row['id']}/review",headers=self.headers(self.other),json=payload).status_code,403)
        result=self.client.post(f"/admin/data-requests/{row['id']}/review",headers=self.headers(self.admin),json=payload)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['status'],'restricted_pending_erasure')
        self.assertIn('does not mean all data',result.json()['explanation'])
        self.assertIsNotNone(result.json()['retention_until'])
        self.assertEqual(self.client.get('/auth/me',headers=self.headers(self.owner)).status_code,401)
        self.assertEqual(self.client.post('/auth/login',json=self.owner['credentials']).status_code,401)
        self.assertEqual(self.client.post(f"/admin/data-requests/{row['id']}/review",headers=self.headers(self.admin),json=payload).status_code,409)

    def test_request_owner_cross_college_duplicate_and_withdrawal(self):
        row=self.request()
        self.assertEqual(self.client.get('/account/data-requests',headers=self.headers(self.other)).json(),[])
        self.assertEqual(self.client.post(f"/account/data-requests/{row['id']}/withdraw",headers=self.headers(self.other)).status_code,404)
        self.assertEqual(self.client.post('/account/data-requests',headers=self.headers(self.owner),json={'reason':'Second duplicate request','confirmation':'REQUEST DELETION'}).status_code,409)
        self.assertEqual(self.client.post(f"/account/data-requests/{row['id']}/withdraw",headers=self.headers(self.owner)).json()['status'],'withdrawn')
        with tenant_session(10229) as session:
            self.assertEqual(session.scalars(select(DataRequest).where(DataRequest.college_id==10219)).all(),[])
        with engine.connect() as connection:
            self.assertEqual(connection.execute(select(AuthLimit.id)).all(),[])
            self.assertEqual(connection.execute(select(DataRequest.id)).all(),[])

    def test_fixed_window_unknown_login_and_signup_limits(self):
        unknown={'email':uuid.uuid4().hex+'@limited.invalid','college_id':10219,'password':'Local-limit-test-2026'}
        # High fixture allowances are disabled only inside this controlled loopback test.
        with patch.dict(os.environ,{'ALLOW_TEST_DATABASE':'no'}):
            for _ in range(8): self.assertEqual(self.client.post('/auth/login',json=unknown).status_code,401)
            result=self.client.post('/auth/login',json=unknown)
            self.assertEqual(result.status_code,429,result.text);self.assertIn('retry-after',result.headers)
            self.assertEqual(self.client.post('/auth/login',json={**unknown,'college_id':10229}).status_code,401)
            fresh={**unknown,'email':uuid.uuid4().hex+'@limited.invalid','name':'Limit fixture'}
            self.assertEqual(self.client.post('/auth/signup',json=fresh).status_code,201)
            for _ in range(2): self.assertEqual(self.client.post('/auth/signup',json=fresh).status_code,409)
            self.assertEqual(self.client.post('/auth/signup',json=fresh).status_code,429)

    def test_anonymous_data_controls_and_admin_deletion_are_denied(self):
        for path in ('/account/export','/account/data-requests','/admin/data-requests'):
            self.assertEqual(self.client.get(path).status_code,401)
        result=self.client.post('/account/data-requests',headers=self.headers(self.admin),json={'reason':'Administrator fixture deletion request','confirmation':'REQUEST DELETION'})
        self.assertEqual(result.status_code,201,result.text)
        result=self.client.post(f"/admin/data-requests/{result.json()['id']}/review",headers=self.headers(self.admin),json={'action':'restrict','reason':'No successor administrator has been established'})
        self.assertEqual(result.status_code,409)
