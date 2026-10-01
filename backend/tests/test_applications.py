"""Real PostgreSQL integration: directory identity, consent, audit and FORCE RLS."""
import json
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import select, func, update
from sqlalchemy.exc import DBAPIError
from colleges import DIRECTORY
from database import engine, tenant_session, SessionLocal
from main import app
from datetime import datetime, timezone
from models import AccountAccess, Application, ApplicationEvent, Match, Notification, Job

class ApplicationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("127.0.0.1", "localhost"):
            raise RuntimeError("Explicit localhost test database required.")
        cls.client = TestClient(app)
        cls.client.__enter__()
        cls.colleges = [c["id"] for c in DIRECTORY["colleges"] if c["kind"] == "bput_directory"][:2]
        cls.accounts = []
        cls.recruiters = []
        cls.jobs = []
        for college in [cls.colleges[0], cls.colleges[1], cls.colleges[0]]:
            credentials = dict(email=f"{uuid.uuid4().hex}@applications.test", password="Synthetic-test-only-2026", college_id=college)
            r = cls.client.post("/auth/signup", json={**credentials, "name": "Synthetic application check"})
            assert r.status_code == 201, r.text
            result = r.json()
            with tenant_session(college) as session:
                session.add(AccountAccess(college_id=college, user_id=result["user"]["user_id"], email_verified_at=datetime.now(timezone.utc), approval_status="approved"))
            cls.accounts.append((credentials, result["user"], {"Authorization": "Bearer " + result["access_token"]}))
        for college in [cls.colleges[0], cls.colleges[1], cls.colleges[0]]:
            r = cls.client.post("/auth/recruiter/signup", json=dict(email=f"{uuid.uuid4().hex}@applications.test",
                password="Synthetic-test-only-2026", college_id=college, company=dict(name="Synthetic application company", industry="Testing")))
            assert r.status_code == 201, r.text
            with tenant_session(college) as session:
                session.add(AccountAccess(college_id=college, user_id=r.json()["user"]["user_id"], email_verified_at=datetime.now(timezone.utc), approval_status="approved"))
            headers = {"Authorization": "Bearer " + r.json()["access_token"]}
            cls.recruiters.append(headers)
            drives = []
            for index in range(5 if college == cls.colleges[0] else 1):
                r = cls.client.post("/recruiters/jobs", headers=headers, json=dict(title=f"Synthetic application drive {index}",
                    ctc=6, min_cgpa=8, eligible_branches=["CSE"], required_skills=[dict(skill_name="python", min_proficiency=70)]))
                assert r.status_code == 201, r.text
                drives.append(r.json()["id"])
            cls.jobs.append(drives)
        _, user, cls.headers = cls.accounts[0]
        cls.path = f"/students/{user['student_id']}/applications"

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def submit(self, job):
        r = self.client.post(self.path, headers=self.headers, json={"job_id": job, "cover_note": "Synthetic test submission"})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def test_directory_parity_and_login_non_demo_colleges(self):
        data = self.client.get("/colleges").json()
        self.assertEqual(data, DIRECTORY)
        front = json.loads((Path(__file__).parents[2] / "frontend/src/assets/bput-colleges.json").read_text(encoding="utf-8"))
        self.assertEqual(front, data)
        self.assertEqual(len([c for c in data["colleges"] if c["kind"] == "bput_directory"]), 169)
        self.assertEqual([c["id"] for c in data["colleges"] if c["kind"] == "demo"], [1, 2])
        self.assertIn("2022", data["source_year"])
        for credentials, user, headers in self.accounts:
            r = self.client.post("/auth/login", json=credentials)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()["user"]["college_id"], credentials["college_id"])
            self.assertTrue(r.json()["user"]["college_name"])
            self.assertEqual(self.client.get("/auth/me", headers=headers).status_code, 200)
        credentials = self.accounts[0][0]
        self.assertEqual(self.client.post("/auth/login", json={**credentials, "college_id": self.colleges[1]}).status_code, 401)
        for value in [999999, True, "1"]:
            self.assertEqual(self.client.post("/auth/login", json={**credentials, "college_id": value}).status_code, 422)

    def test_submission_frozen_evidence_and_duplicate_handling(self):
        before = self.count_matches()
        row = self.submit(self.jobs[0][0])
        self.assertFalse(row["evidence"]["eligible"])
        self.assertEqual(len(row["evidence"]["factor_breakdown"]), 5)
        self.assertTrue(row["evidence"]["explanation"] and row["evidence"]["next_step"])
        self.assertEqual(len(row["history"]), 1)
        self.assertEqual(row["history"][0]["status"], "submitted")
        self.assertEqual(self.client.post(self.path, headers=self.headers, json={"job_id": row["job_id"]}).status_code, 409)
        with tenant_session(self.colleges[0]) as session:
            session.execute(update(Job).where(Job.id == row["job_id"], Job.college_id == self.colleges[0]).values(min_cgpa=0))
        saved = self.client.get(self.path, headers=self.headers).json()["items"]
        self.assertEqual(next(a for a in saved if a["id"] == row["id"])["evidence"], row["evidence"])
        self.assertEqual(before, self.count_matches())
        with tenant_session(self.colleges[0]) as session:
            notes = session.scalars(select(Notification).where(Notification.college_id == self.colleges[0],
                Notification.event_key == f"application:{row['id']}:1")).all()
            self.assertEqual(len(notes), 2)

    def count_matches(self):
        with tenant_session(self.colleges[0]) as session:
            return session.scalar(select(func.count()).select_from(Match).where(Match.college_id == self.colleges[0]))

    def test_recruiter_review_stale_version_and_student_withdrawal(self):
        row = self.submit(self.jobs[0][1])
        path = f"/recruiters/jobs/{row['job_id']}/applications/{row['id']}/review"
        payload = dict(version=1, status="shortlisted", reason="Human review of synthetic evidence")
        r = self.client.post(path, headers=self.recruiters[0], json=payload)
        self.assertEqual(r.status_code, 200, r.text)
        reviewed = r.json()
        self.assertEqual((reviewed["status"], reviewed["version"]), ("shortlisted", 2))
        self.assertEqual(reviewed["evidence"], row["evidence"])
        self.assertEqual(self.client.post(path, headers=self.recruiters[0], json=payload).status_code, 409)
        withdrawal = f"{self.path}/{row['id']}/withdraw"
        r = self.client.post(withdrawal, headers=self.headers, json=dict(version=2, reason="Student withdraws test application"))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual([e["status"] for e in r.json()["history"]], ["submitted", "shortlisted", "withdrawn"])
        self.assertEqual(self.client.post(path, headers=self.recruiters[0], json={**payload, "version": 3}).status_code, 409)
        self.assertEqual(self.client.post(withdrawal, headers=self.headers, json=dict(version=3, reason="Attempt another withdrawal")).status_code, 409)

    def test_ownership_filters_role_denials_and_validation(self):
        row = self.submit(self.jobs[0][2])
        path = f"/recruiters/jobs/{row['job_id']}/applications/{row['id']}/review"
        review = dict(version=1, status="rejected", reason="Synthetic reviewer decision")
        self.assertEqual(self.client.get(self.path).status_code, 401)
        self.assertEqual(self.client.get(self.path, headers=self.recruiters[0]).status_code, 403)
        for _, user, headers in self.accounts[1:]:
            self.assertEqual(self.client.get(self.path, headers=headers).status_code, 404)
            self.assertEqual(self.client.post(f"/students/{user['student_id']}/applications/{row['id']}/withdraw",
                headers=headers, json=dict(version=1, reason="Wrong account withdrawal")).status_code, 404)
        for headers in self.recruiters[1:]:
            self.assertEqual(self.client.post(path, headers=headers, json=review).status_code, 404)
        self.assertEqual(self.client.post(path, headers=self.headers, json=review).status_code, 403)
        self.assertEqual(self.client.post(self.path, headers=self.headers, json={"job_id": self.jobs[1][0]}).status_code, 404)
        for payload in [{"job_id": 0}, {"job_id": row["job_id"], "college_id": self.colleges[1]}, {"job_id": row["job_id"], "status": "shortlisted"}]:
            self.assertEqual(self.client.post(self.path, headers=self.headers, json=payload).status_code, 422)
        self.assertEqual(self.client.post(path, headers=self.recruiters[0], json={**review, "reason": " "}).status_code, 422)
        self.assertEqual(self.client.post(path, headers=self.recruiters[0], json=review).status_code, 200)
        self.assertEqual(self.client.post(f"{self.path}/{row['id']}/withdraw", headers=self.headers,
            json=dict(version=2, reason="Withdraw after rejection")).status_code, 409)
        listed = self.client.get(f"/recruiters/jobs/{row['job_id']}/applications", headers=self.recruiters[0], params={"limit": 1}).json()
        self.assertEqual(listed["items"][0]["id"], row["id"])
        self.assertEqual(listed["total"], 1)
        self.assertEqual(self.client.get(self.path, headers=self.headers, params={"limit": 51}).status_code, 422)
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/students/{student_id}/applications", schema["paths"])
        self.assertIn("/recruiters/jobs/{job_id}/applications/{application_id}/review", schema["paths"])

    def test_force_rls_fail_closed_and_cross_college_write_blocked(self):
        row = self.submit(self.jobs[0][3])
        # Deliberately omit application filters to exercise the second enforcement layer.
        with tenant_session(self.colleges[1]) as session:
            self.assertNotIn(row["id"], session.scalars(select(Application.id)).all())
            self.assertTrue(all(e.college_id == self.colleges[1] for e in session.scalars(select(ApplicationEvent))))
        with SessionLocal() as session:
            self.assertEqual(session.scalars(select(Application)).all(), [])
            self.assertEqual(session.scalars(select(ApplicationEvent)).all(), [])
        with self.assertRaises(DBAPIError):
            with tenant_session(self.colleges[1]) as session:
                session.add(Application(college_id=self.colleges[0], student_id=row["student_id"],
                    job_id=self.jobs[0][3], evidence_snapshot={}))
                session.flush()
        health = self.client.get("/health").json()
        policies = {t["table"]: t for t in health["isolation"]["tables"]}
        for table in ["applications", "application_events"]:
            self.assertEqual(policies[table]["status"], "verified")
            self.assertTrue(policies[table]["forced"] and policies[table]["enabled"])

    def test_concurrent_duplicate_submissions_create_one_audited_record(self):
        job = self.jobs[0][4]
        def send(_):
            return self.client.post(self.path, headers=self.headers, json={"job_id": job})
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(send, range(2)))
        self.assertEqual(sorted(r.status_code for r in responses), [201, 409])
        row = next(r.json() for r in responses if r.status_code == 201)
        with tenant_session(self.colleges[0]) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(Application).where(
                Application.college_id == self.colleges[0], Application.student_id == row["student_id"],
                Application.job_id == job)), 1)
            self.assertEqual(session.scalar(select(func.count()).select_from(ApplicationEvent).where(
                ApplicationEvent.college_id == self.colleges[0], ApplicationEvent.application_id == row["id"])), 1)
