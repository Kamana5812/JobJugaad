"""Local PostgreSQL account admission tests. Email transport mocked; no delivery claim."""
import hashlib
import io
import json
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError
from database import engine, initialize_schema, tenant_session
from main import app
from models import User, AccountAccess, AccountAccessEvent, EmailVerificationToken
from engines import email_delivery

class AccountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("localhost", "127.0.0.1"):
            raise RuntimeError("Explicit localhost test database required.")
        initialize_schema()
        cls.client = TestClient(app)

    def setUp(self):
        self.college = 10219
        self.student = self.signup()
        self.admin = self.signup()
        with tenant_session(self.college) as session:
            session.execute(update(User).where(User.college_id == self.college, User.id == self.admin["user"]["user_id"]).values(role="admin"))
            session.add(AccountAccess(college_id=self.college, user_id=self.admin["user"]["user_id"], email_verified_at=datetime.now(timezone.utc)))
        self.allowlist = patch.dict(os.environ, {"ADMIN_ACCOUNTS": json.dumps([{"email": self.admin["user"]["email"], "college_id": self.college}])})
        self.allowlist.start(); self.addCleanup(self.allowlist.stop)
        result = self.client.post("/auth/login", json=self.admin["credentials"])
        self.assertEqual(result.status_code, 200, result.text)
        self.admin_headers = self.headers(result.json())

    def headers(self, result):
        return {"Authorization": "Bearer " + result["access_token"]}

    def signup(self, role="student", college=10219):
        credentials = dict(email=uuid.uuid4().hex + "@account-test.invalid", password="Local-account-test-2026", college_id=college)
        body = {**credentials, "name": "Local account test"} if role == "student" else {**credentials, "company": {"name": "Local workflow company", "industry": "Testing"}}
        result = self.client.post("/auth/signup" if role == "student" else "/auth/recruiter/signup", json=body)
        self.assertEqual(result.status_code, 201, result.text)
        return {**result.json(), "credentials": credentials}

    def send(self, account):
        with patch.object(email_delivery, "configured", return_value=True), patch.object(email_delivery, "send_verification") as send:
            result = self.client.post("/auth/email-verification", headers=self.headers(account))
            self.assertEqual(result.status_code, 200, result.text)
            self.assertNotIn("token", result.json())
            link = send.call_args.args[1]
            return parse_qs(urlparse(link).fragment)["token"][0]

    def verify(self, account):
        token = self.send(account)
        result = self.client.post("/auth/verify-email", json={"college_id": account["user"]["college_id"], "token": token})
        self.assertEqual(result.status_code, 200, result.text)
        return token

    def approve(self, account):
        self.verify(account)
        result = self.client.post("/auth/access", headers=self.headers(account), json={"consent": True, "affiliation_reference": "LOCAL TEST", "context": "Test fixture only"})
        self.assertEqual(result.status_code, 200, result.text)
        row = result.json()
        result = self.client.post(f"/admin/accounts/{row['id']}/review", headers=self.admin_headers,
            json={"version": row["version"], "status": "approved", "reason": "Local fixture affiliation checked"})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def test_verification_approval_revocation_and_audit(self):
        headers = self.headers(self.student)
        profile = f"/students/{self.student['user']['student_id']}"
        self.assertEqual(self.client.get(profile, headers=headers).status_code, 403)
        self.assertEqual(self.client.post("/auth/access", headers=headers, json={"consent": True, "affiliation_reference": "TEST"}).status_code, 403)
        approved = self.approve(self.student)
        self.assertEqual(self.client.get(profile, headers=headers).status_code, 200)
        self.assertEqual(self.client.get("/auth/me", headers=headers).json()["access_status"], "approved")
        stale = {"version": approved["version"]-1, "status": "rejected", "reason": "Local revoke check"}
        self.assertEqual(self.client.post(f"/admin/accounts/{approved['id']}/review", headers=self.admin_headers, json=stale).status_code, 409)
        stale["version"] = approved["version"]
        revoked = self.client.post(f"/admin/accounts/{approved['id']}/review", headers=self.admin_headers, json=stale)
        self.assertEqual(revoked.status_code, 200, revoked.text)
        self.assertEqual(self.client.get(profile, headers=headers).status_code, 403)
        self.assertEqual([e["action"] for e in revoked.json()["history"]], ["email_verified", "requested", "approved", "rejected"])

    def test_hashed_challenge_expiry_wrong_tenant_and_rate_limit(self):
        token = self.send(self.student)
        with tenant_session(self.college) as session:
            row = session.scalar(select(EmailVerificationToken).where(EmailVerificationToken.college_id == self.college,
                EmailVerificationToken.user_id == self.student["user"]["user_id"]))
            self.assertEqual(row.token_hash, hashlib.sha256(token.encode()).hexdigest())
            self.assertNotEqual(row.token_hash, token)
            session.execute(update(EmailVerificationToken).where(EmailVerificationToken.college_id == self.college, EmailVerificationToken.id == row.id).values(expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)))
        with patch.object(email_delivery, "configured", return_value=True), patch.object(email_delivery, "send_verification") as send:
            self.assertEqual(self.client.post("/auth/email-verification", headers=self.headers(self.student)).status_code, 429)
            send.assert_not_called()
        body = {"college_id": 10220, "token": token}
        self.assertEqual(self.client.post("/auth/verify-email", json=body).status_code, 400)
        body["college_id"] = self.college
        self.assertEqual(self.client.post("/auth/verify-email", json=body).status_code, 410)
        with tenant_session(10220) as session:
            self.assertIsNone(session.scalar(select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hashlib.sha256(token.encode()).hexdigest())))

    def test_disabled_delivery_demo_signup_and_consent_fail_closed(self):
        with patch.object(email_delivery, "configured", return_value=False):
            self.assertEqual(self.client.post("/auth/email-verification", headers=self.headers(self.student)).status_code, 503)
        with patch.dict(os.environ, {"ALLOW_DEMO_SIGNUPS": "no"}):
            for path, body in [("/auth/signup", {"name": "Test"}), ("/auth/recruiter/signup", {"company": {"name": "Test", "industry": "Testing"}})]:
                result = self.client.post(path, json={**body, "email": "local@example.invalid", "password": "Local-account-test-2026", "college_id": 1})
                self.assertEqual(result.status_code, 403, result.text)
        self.verify(self.student)
        self.assertEqual(self.client.post("/auth/access", headers=self.headers(self.student), json={"consent": False, "affiliation_reference": "TEST"}).status_code, 422)
        self.assertEqual(self.client.get("/admin/accounts", headers=self.headers(self.student)).status_code, 403)

    def test_approval_queue_and_new_tables_enforce_tenant_scope(self):
        row = self.approve(self.student)
        for model in (AccountAccess, AccountAccessEvent, EmailVerificationToken):
            with tenant_session(10220) as session:
                self.assertEqual(session.scalars(select(model).where(model.college_id == self.college)).all(), [])
        invalid_rows = [AccountAccess(college_id=self.college, user_id=self.student["user"]["user_id"]),
            AccountAccessEvent(college_id=self.college, access_id=row["id"], actor_user_id=self.admin["user"]["user_id"], action="test", reason="Must fail RLS"),
            EmailVerificationToken(college_id=self.college, user_id=self.student["user"]["user_id"], token_hash=uuid.uuid4().hex*2, expires_at=datetime.now(timezone.utc)+timedelta(hours=1))]
        for invalid in invalid_rows:
            with self.assertRaises(DBAPIError) as blocked, tenant_session(10220) as session:
                session.add(invalid); session.flush()
            self.assertIn("row-level security", str(blocked.exception).lower())
        outsider = self.signup(college=10220)
        self.verify(outsider)
        request = self.client.post("/auth/access", headers=self.headers(outsider), json={"consent": True, "affiliation_reference": "OTHER COLLEGE"})
        self.assertEqual(request.status_code, 200, request.text)
        other = request.json()
        queue = self.client.get("/admin/accounts", headers=self.admin_headers)
        self.assertEqual(queue.status_code, 200, queue.text)
        self.assertNotIn(other["id"], [i["id"] for i in queue.json()["items"]])
        decision = self.client.post(f"/admin/accounts/{other['id']}/review", headers=self.admin_headers,
            json={"version": other["version"], "status": "approved", "reason": "Must not cross tenants"})
        self.assertEqual(decision.status_code, 404)

    def test_replaced_challenge_and_delivery_failure(self):
        first = self.send(self.student)
        with tenant_session(self.college) as session:
            session.execute(update(AccountAccess).where(AccountAccess.college_id == self.college,
                AccountAccess.user_id == self.student["user"]["user_id"]).values(last_email_requested_at=datetime.now(timezone.utc)-timedelta(minutes=2)))
        second = self.send(self.student)
        self.assertNotEqual(first, second)
        self.assertEqual(self.client.post("/auth/verify-email", json={"college_id": self.college, "token": first}).status_code, 400)
        self.assertEqual(self.client.post("/auth/verify-email", json={"college_id": self.college, "token": second}).status_code, 200)
        other = self.signup()
        with patch.object(email_delivery, "configured", return_value=True), patch.object(email_delivery, "send_verification", side_effect=HTTPException(503, "Delivery unavailable")):
            self.assertEqual(self.client.post("/auth/email-verification", headers=self.headers(other)).status_code, 503)
        self.assertEqual(self.client.get("/auth/me", headers=self.headers(other)).json()["access_status"], "unverified")

    def test_duplicate_link_is_idempotent_without_approval(self):
        token = self.verify(self.student)
        result = self.client.post("/auth/verify-email", json={"college_id": self.college, "token": token})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.client.get("/auth/me", headers=self.headers(self.student)).json()["access_status"], "pending")
        self.assertEqual(self.client.get(f"/students/{self.student['user']['student_id']}", headers=self.headers(self.student)).status_code, 403)

    def test_owner_test_mode_does_not_create_other_user_challenge(self):
        values = {"MAIL_FROM": "onboarding@resend.dev", "RESEND_API_KEY": "local-mocked-key",
            "RESEND_TEST_RECIPIENT": self.admin["user"]["email"]}
        with patch.dict(os.environ, values), patch.object(email_delivery, "urlopen") as send:
            headers = self.headers(self.student)
            self.assertFalse(self.client.get("/auth/access", headers=headers).json()["email_delivery_ready"])
            self.assertEqual(self.client.post("/auth/email-verification", headers=headers).status_code, 503)
            with tenant_session(self.college) as session:
                challenges = session.scalars(select(EmailVerificationToken).where(EmailVerificationToken.college_id == self.college,
                    EmailVerificationToken.user_id == self.student["user"]["user_id"])).all()
                self.assertEqual(challenges, [])
            send.assert_not_called()
            with patch.dict(os.environ, {"RESEND_TEST_RECIPIENT": self.student["user"]["email"]}), patch.object(email_delivery, "urlopen", return_value=io.BytesIO(b'{"id":"local-test-message"}')) as accepted:
                self.assertTrue(self.client.get("/auth/access", headers=headers).json()["email_delivery_ready"])
                self.assertEqual(self.client.post("/auth/email-verification", headers=headers).status_code, 200)
                accepted.assert_called_once()
            self.assertEqual(self.client.get("/auth/me", headers=headers).json()["access_status"], "unverified")

    def test_admission_filters_and_shortlist_to_calendar(self):
        recruiter = self.signup("recruiter")
        self.approve(recruiter); self.approve(self.student)
        headers = self.headers(recruiter)
        drive = self.client.post("/recruiters/jobs", headers=headers, json={"title": "Local real-college workflow", "ctc": 6,
            "min_cgpa": 0, "eligible_branches": ["Not set"], "required_skills": [{"skill_name": "python", "min_proficiency": 60}]})
        self.assertEqual(drive.status_code, 201, drive.text)
        job = drive.json()["id"]
        matching = self.client.post(f"/recruiters/jobs/{job}/matching", headers=headers)
        self.assertEqual(matching.status_code, 200, matching.text)
        # Unverified accounts never appear in recruiter ranking, even if they have a student row.
        candidates = self.client.get(f"/recruiters/jobs/{job}/matches?status=all", headers=headers).json()
        self.assertIn(self.student["user"]["student_id"], [c["student_id"] for c in candidates["candidates"]])
        self.assertNotIn(self.admin["user"]["student_id"], [c["student_id"] for c in candidates.get("candidates", [])])
        slot = {"job_id": job, "student_id": self.student["user"]["student_id"], "scheduled_time": "2038-05-01T10:00:00Z", "duration_minutes": 30, "venue": uuid.uuid4().hex, "panel_id": uuid.uuid4().hex}
        self.assertEqual(self.client.post("/admin/schedules", headers=self.admin_headers, json=slot).status_code, 409)
        application = self.client.post(f"/students/{self.student['user']['student_id']}/applications", headers=self.headers(self.student), json={"job_id": job})
        self.assertEqual(application.status_code, 201, application.text)
        row = application.json()
        reviewed = self.client.post(f"/recruiters/jobs/{job}/applications/{row['id']}/review", headers=headers,
            json={"version": row["version"], "status": "shortlisted", "reason": "Recruiter agrees to interview"})
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        proposal = self.client.post("/admin/schedules", headers=self.admin_headers, json=slot)
        self.assertEqual(proposal.status_code, 201, proposal.text)
        p = proposal.json()
        booking = self.client.post(f"/admin/schedules/{p['id']}/review", headers=self.admin_headers,
            json={"version": p["version"], "action": "approve", "reason": "Local approved booking"})
        self.assertEqual(booking.status_code, 200, booking.text)
        calendar = self.client.get(f"/students/{self.student['user']['student_id']}/interviews", headers=self.headers(self.student))
        self.assertEqual(calendar.status_code, 200, calendar.text)
        self.assertTrue(any(i["job_title"] == "Local real-college workflow" for i in calendar.json()["items"]))
        interview = next(i for i in calendar.json()["items"] if i["job_id"] == job)
        # Move only the status-checker's clock past this local booking; no live records are edited.
        with patch("engines.scheduling.datetime") as clock:
            clock.now.return_value = datetime.fromisoformat(interview["end_time"])+timedelta(minutes=1)
            selected = self.client.put(f"/admin/interviews/{interview['id']}/status", headers=self.admin_headers,
                json={"status": "selected", "reason": "Local human outcome fixture"})
        self.assertEqual(selected.status_code, 200, selected.text)
        offer = self.client.post("/admin/offers", headers=self.admin_headers, json={"interview_id": interview["id"], "reason": "Local selected interview offer"})
        self.assertEqual(offer.status_code, 201, offer.text)
        row = offer.json()
        for role, stage, value in [("admin", "offer_letter_status", "issued"), ("student", "action", "accept"),
            ("student", "action", "submit_documents"), ("admin", "verification_status", "verified"), ("admin", "joining_status", "joined")]:
            payload = {"version": row["version"], "reason": "Local explicit lifecycle action"}
            if role == "admin":
                response = self.client.put(f"/admin/offers/{row['id']}", headers=self.admin_headers, json={**payload, "stage": stage, "value": value})
            else:
                response = self.client.post(f"/students/{self.student['user']['student_id']}/offers/{row['id']}/actions", headers=self.headers(self.student), json={**payload, "action": value})
            self.assertEqual(response.status_code, 200, response.text)
            row = response.json()
        self.assertEqual(row["joining_status"], "joined")
        self.assertFalse(row["is_synthetic"])
        self.assertEqual(len(row["audit"]), 6)
        analytics = self.client.get("/admin/analytics/overview", headers=self.admin_headers)
        self.assertEqual(analytics.status_code, 200, analytics.text)
        self.assertGreaterEqual(analytics.json()["joined_students"], 1)
        self.assertEqual(analytics.json()["synthetic_offer_count"], 0)
        notifications = self.client.get("/notifications", headers=self.headers(self.student)).json()
        self.assertTrue(all(n["delivery"] == "in_app" for n in notifications["notifications"]))

class ResendAdapterTests(unittest.TestCase):
    values = {"MAIL_FROM": "accounts@example.invalid", "RESEND_API_KEY": "local-mocked-key",
        "RESEND_TEST_RECIPIENT": ""}

    def test_https_payload_and_challenge_idempotency(self):
        response = io.BytesIO(json.dumps({"id": "test-message"}).encode())
        with patch.dict(os.environ, self.values), patch.object(email_delivery, "urlopen", return_value=response) as send:
            self.assertTrue(email_delivery.configured("recipient@example.invalid"))
            email_delivery.send_verification("recipient@example.invalid", "https://jobjugaad.vercel.app/verify-email#token=test", "verification:10219:42")
            request = send.call_args.args[0]
            self.assertEqual(request.full_url, "https://api.resend.com/emails")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(send.call_args.kwargs["timeout"], 15)
            headers = {k.lower(): v for k, v in request.header_items()}
            self.assertEqual(headers["authorization"], "Bearer local-mocked-key")
            self.assertEqual(headers["idempotency-key"], "verification:10219:42")
            body = json.loads(request.data)
            self.assertEqual(body["from"], "JobJugaad <accounts@example.invalid>")
            self.assertEqual(body["to"], ["recipient@example.invalid"])
            self.assertIn("token=test", body["text"])
            self.assertIn("does not confirm college affiliation", body["text"])
            self.assertNotIn("local-mocked-key", str(body))
            send.assert_called_once()

    def test_default_sender_requires_explicit_owner_and_blocks_other_recipients(self):
        values = {**self.values, "MAIL_FROM": "onboarding@resend.dev", "RESEND_TEST_RECIPIENT": "owner@example.invalid"}
        with patch.dict(os.environ, values), patch.object(email_delivery, "urlopen") as send:
            self.assertTrue(email_delivery.configured())
            self.assertTrue(email_delivery.configured("OWNER@example.invalid"))
            self.assertFalse(email_delivery.configured("other@example.invalid"))
            with self.assertRaises(HTTPException) as error:
                email_delivery.send_verification("other@example.invalid", "test", "test")
            self.assertEqual(error.exception.status_code, 503)
            send.assert_not_called()
            with patch.dict(os.environ, {"RESEND_TEST_RECIPIENT": ""}):
                self.assertFalse(email_delivery.configured())

    def test_missing_secret_and_invalid_sender_fail_closed(self):
        for update in [{"RESEND_API_KEY": ""}, {"MAIL_FROM": "kamnaa313@gmail.com"},
            {"MAIL_FROM": "bad\naddress@example.invalid"}, {"MAIL_FROM": ""},
            {"MAIL_FROM": "other@resend.dev", "RESEND_TEST_RECIPIENT": "owner@example.invalid"}]:
            with self.subTest(update=update), patch.dict(os.environ, {**self.values, **update}), patch.object(email_delivery, "urlopen") as send:
                self.assertFalse(email_delivery.configured())
                with self.assertRaises(HTTPException):
                    email_delivery.send_verification("recipient@example.invalid", "test", "test")
                send.assert_not_called()

    def test_provider_failures_are_generic_and_leave_no_delivery_claim(self):
        failures = [OSError("private provider detail"),
            HTTPError("https://api.resend.com/emails", 403, "private", {}, io.BytesIO(b"secret provider body"))]
        for failure in failures:
            with self.subTest(error=type(failure).__name__), patch.dict(os.environ, self.values), patch.object(email_delivery, "urlopen", side_effect=failure):
                with self.assertRaises(HTTPException) as error:
                    email_delivery.send_verification("recipient@example.invalid", "test", "test")
                self.assertEqual(error.exception.status_code, 503)
                self.assertNotIn("private", error.exception.detail)
                self.assertNotIn("local-mocked-key", error.exception.detail)
        for payload in [b"not JSON", b"[]", b"{}", b'{"id": null}', b'{"id": ""}']:
            with self.subTest(payload=payload), patch.dict(os.environ, self.values), patch.object(email_delivery, "urlopen", return_value=io.BytesIO(payload)):
                with self.assertRaises(HTTPException) as error:
                    email_delivery.send_verification("recipient@example.invalid", "test", "test")
                self.assertEqual(error.exception.status_code, 503)
