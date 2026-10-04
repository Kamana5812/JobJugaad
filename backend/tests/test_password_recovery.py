"""Disposable localhost accounts; email delivery mocked, never real inbox claims."""
import hashlib
import base64
import io
import json
from email import message_from_bytes
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from database import engine, initialize_schema, tenant_session, isolation_report
from models import PasswordResetToken, User
from main import app
from engines import email_delivery
from auth import signing_secret, ISSUER, AUDIENCE
from jose import jwt


class PasswordRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('ALLOW_TEST_DATABASE') != 'yes' or engine.url.host not in ('127.0.0.1', 'localhost'):
            raise RuntimeError('Explicit localhost test database required.')
        initialize_schema()
        cls.client = TestClient(app)

    def setUp(self):
        self.credentials = {'college_id': 10219, 'email': uuid.uuid4().hex + '@recovery-test.invalid', 'password': 'Local-recovery-old-2026'}
        result = self.client.post('/auth/signup', json={**self.credentials, 'name': 'Disposable recovery fixture'})
        self.assertEqual(result.status_code, 201, result.text)
        self.account = result.json()
        self.headers = {'Authorization': 'Bearer ' + self.account['access_token']}

    def request(self):
        with patch.object(email_delivery, 'configured', return_value=True), patch.object(email_delivery, 'send_password_reset') as send:
            result = self.client.post('/auth/password-reset-request', json={key: self.credentials[key] for key in ('email', 'college_id')})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn('token', result.json())
        token = parse_qs(urlparse(send.call_args.args[1]).fragment)['token'][0]
        return token

    def reset(self, token, college=10219):
        return self.client.post('/auth/reset-password', json={'college_id': college, 'token': token, 'password': 'Local-recovery-new-2026'})

    def test_single_use_hash_and_session_invalidation(self):
        token = self.request()
        with tenant_session(10219) as session:
            row = session.scalar(select(PasswordResetToken).where(PasswordResetToken.college_id == 10219, PasswordResetToken.user_id == self.account['user']['user_id']))
            self.assertEqual(row.token_hash, hashlib.sha256(token.encode()).hexdigest())
            self.assertEqual(row.delivery_status, 'accepted')
        self.assertEqual(self.reset(token).status_code, 200)
        self.assertEqual(self.reset(token).status_code, 400)
        self.assertEqual(self.client.get('/auth/me', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post('/auth/email-verification', headers=self.headers).status_code, 401)
        self.assertEqual(self.client.post('/auth/login', json=self.credentials).status_code, 401)
        result = self.client.post('/auth/login', json={**self.credentials, 'password': 'Local-recovery-new-2026'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['user']['role'], 'student')
        self.assertEqual(result.json()['user']['access_status'], self.account['user']['access_status'])

    def test_expired_and_wrong_college_links_cannot_reset(self):
        token = self.request()
        self.assertEqual(self.reset(token, 10229).status_code, 400)
        with tenant_session(10219) as session:
            session.execute(update(PasswordResetToken).where(PasswordResetToken.college_id == 10219, PasswordResetToken.user_id == self.account['user']['user_id']).values(expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)))
        self.assertEqual(self.reset(token).status_code, 400)
        self.assertEqual(self.client.post('/auth/login', json=self.credentials).status_code, 200)

    def test_replacement_and_quota(self):
        first = self.request()
        payload = {key: self.credentials[key] for key in ('email', 'college_id')}
        self.assertEqual(self.client.post('/auth/password-reset-request', json=payload).status_code, 429)
        with tenant_session(10219) as session:
            session.execute(update(PasswordResetToken).where(PasswordResetToken.college_id == 10219, PasswordResetToken.user_id == self.account['user']['user_id']).values(created_at=datetime.now(timezone.utc)-timedelta(minutes=2)))
        second = self.request()
        self.assertEqual(self.reset(first).status_code, 400)
        self.assertEqual(self.reset(second).status_code, 200)

    def test_unknown_and_unconfigured_have_same_generic_response(self):
        with patch.object(email_delivery, 'configured', return_value=False), patch.object(email_delivery, 'send_password_reset') as send:
            known = self.client.post('/auth/password-reset-request', json={key: self.credentials[key] for key in ('email', 'college_id')})
            unknown = self.client.post('/auth/password-reset-request', json={'email': uuid.uuid4().hex + '@unknown.invalid', 'college_id': 10219})
            self.assertEqual(known.status_code, 200)
            self.assertEqual(known.json(), unknown.json())
            send.assert_not_called()

    def test_parallel_consumption_only_one_succeeds(self):
        token = self.request()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.reset(token).status_code, range(2)))
        self.assertEqual(sorted(results), [200, 400])

    def test_delivery_failure_is_not_exposed_and_rls_enabled(self):
        with patch.object(email_delivery, 'configured', return_value=True), patch.object(email_delivery, 'send_password_reset', side_effect=RuntimeError('mock transport failure')):
            result = self.client.post('/auth/password-reset-request', json={key: self.credentials[key] for key in ('email', 'college_id')})
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('failure', result.text)
        with tenant_session(10219) as session:
            row = session.scalar(select(PasswordResetToken).where(PasswordResetToken.college_id == 10219, PasswordResetToken.user_id == self.account['user']['user_id']))
            self.assertEqual(row.delivery_status, 'failed')
        with engine.connect() as connection:
            self.assertEqual(connection.execute(select(PasswordResetToken.id)).all(), [])
        self.assertIsNotNone(isolation_report())

    def test_invalid_password_and_token_are_rejected(self):
        token = self.request()
        for password in ('short', 'é' * 40, 'abcdefghij\0'):
            result = self.client.post('/auth/reset-password', json={'college_id': 10219, 'token': token, 'password': password})
            self.assertEqual(result.status_code, 422, result.text)
        self.assertEqual(self.reset('invalid').status_code, 422)
        self.assertEqual(self.client.post('/auth/login', json=self.credentials).status_code, 200)

    def test_admin_role_and_legacy_session_are_preserved_then_revoked(self):
        with tenant_session(10219) as session:
            session.execute(update(User).where(User.college_id == 10219, User.id == self.account['user']['user_id']).values(role='admin'))
        with patch.dict(os.environ, {'ADMIN_ACCOUNTS': json.dumps([{'email': self.credentials['email'], 'college_id': 10219}])}):
            account = self.client.post('/auth/login', json=self.credentials).json()
            claims = jwt.decode(account['access_token'], signing_secret(), algorithms=['HS256'], issuer=ISSUER, audience=AUDIENCE)
            claims.pop('token_version')
            legacy = {'Authorization': 'Bearer ' + jwt.encode(claims, signing_secret(), algorithm='HS256')}
            self.assertEqual(self.client.get('/auth/me', headers=legacy).status_code, 200)
            self.assertEqual(self.reset(self.request()).status_code, 200)
            self.assertEqual(self.client.get('/auth/me', headers=legacy).status_code, 401)
            renewed = self.client.post('/auth/login', json={**self.credentials, 'password': 'Local-recovery-new-2026'})
            self.assertEqual(renewed.status_code, 200, renewed.text)
            self.assertEqual(renewed.json()['user']['role'], 'admin')

    def test_gmail_reset_subject_and_fragment_link(self):
        values = {'EMAIL_PROVIDER': 'gmail', 'MAIL_FROM': 'local-owner@gmail.com', 'GMAIL_CLIENT_ID': 'test-client',
            'GMAIL_CLIENT_SECRET': 'test-secret', 'GMAIL_REFRESH_TOKEN': 'test-refresh'}
        responses = [io.BytesIO(b'{"access_token":"test-access"}'), io.BytesIO(b'{"id":"local-message"}')]
        with patch.dict(os.environ, values), patch.object(email_delivery, 'urlopen', side_effect=responses) as send:
            email_delivery.send_password_reset(self.credentials['email'], 'https://jobjugaad.vercel.app/reset-password#college_id=10219&token=local-test', 'local-reset-test')
        mime = message_from_bytes(base64.urlsafe_b64decode(json.loads(send.call_args.args[0].data)['raw']))
        self.assertEqual(mime['Subject'], 'Reset your JobJugaad password')
        self.assertEqual(mime['To'], self.credentials['email'])
        self.assertIn('/reset-password#', mime.get_payload(decode=True).decode())
