"""Local PostgreSQL targeting, publication, feed ownership, and FORCE RLS tests.

Admission and hiring records are controlled fixtures. No real users, live
notifications, email delivery, or external message service are touched.
"""
import json
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, insert, select, text, update
from sqlalchemy.exc import DBAPIError

from auth import hash_password, issue_token
from database import SessionLocal, engine, initialize_schema, tenant_session
from engines import announcements
from engines.matching import calculate_match
from engines.profile import collections
from main import app
from models import (AccountAccess, AnnouncementRecipient, Application, Company,
    DriveAnnouncement, Interview, Job, Match, Notification, Schedule, Student, User)
from schemas import JobInput


def application_fixture_snapshot(session, student, job, company):
    """Use normal submission's complete weighted-rule evidence for local fixtures."""
    evidence = collections(session, student)
    calculation = calculate_match(student, evidence["skills"], evidence["projects"], evidence["certifications"], job)
    return dict(calculation=calculation.model_dump(mode="json"), student_name=student.name,
        job_title=job.title, company_name=company.name)


class AnnouncementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine is None or engine.url.host not in ("localhost", "127.0.0.1"):
            raise RuntimeError("Explicit localhost test database required.")
        initialize_schema()
        cls.client = TestClient(app)
        cls.suffix = uuid.uuid4().hex[:12]
        cls.branch = "CSE " + cls.suffix.upper()
        cls.other_branch = "ECE " + cls.suffix.upper()
        cls.fixture_password = "Local-announcement-fixture-2026"
        cls.password_hash = hash_password(cls.fixture_password)
        cls.accounts = []
        for college in (10224, 10225):
            account = {"college": college, "students": {}}
            with tenant_session(college) as session:
                account["admin"] = cls.make_person(session, college, "admin", "admin", profile=True)
                account["recruiter"] = cls.make_person(session, college, "recruiter", "recruiter")
                account["pending_recruiter"] = cls.make_person(session, college, "pending-recruiter", "recruiter", "pending")
                for label, role in (("recruiter", "recruiter"), ("pending_recruiter", "pending-recruiter")):
                    company = Company(college_id=college, recruiter_user_id=account[label]["user_id"],
                        name=f"Local announcement company {role} {cls.suffix}", industry="Testing")
                    session.add(company); session.flush()
                    account[label]["company_id"] = company.id
                    account[label]["company_name"] = company.name
                for index in range(12):
                    label = "p" + str(index)
                    account["students"][label] = cls.make_person(session, college, label, "student")
                account["students"]["other"] = cls.make_person(session, college, "other", "student", branch=cls.other_branch)
                for state in ("unverified", "pending", "rejected"):
                    account["students"][state] = cls.make_person(session, college, state, "student", state)
            cls.accounts.append(account)
        cls.allowlist = patch.dict(os.environ, {"ADMIN_ACCOUNTS": json.dumps([
            dict(email=a["admin"]["email"], college_id=a["college"]) for a in cls.accounts])})
        cls.allowlist.start()

    @classmethod
    def tearDownClass(cls):
        cls.allowlist.stop()

    @classmethod
    def make_person(cls, session, college, label, role, status="approved", branch=None, profile=False):
        user = User(college_id=college, email=f"announcements-{label}-{cls.suffix}-{college}@test.invalid",
            password_hash=cls.password_hash, role=role)
        session.add(user); session.flush()
        session.add(AccountAccess(college_id=college, user_id=user.id,
            email_verified_at=None if status == "unverified" else datetime.now(timezone.utc),
            approval_status="pending" if status == "unverified" else status))
        session.flush()
        student = None
        if role == "student" or profile:
            student = Student(college_id=college, user_id=user.id, name=f"Local announcement {label} {cls.suffix}",
                branch=branch or cls.branch, cgpa=8)
            session.add(student); session.flush()
        token = issue_token(user, student=student, session=session).access_token
        return dict(user_id=user.id, student_id=student.id if student else None, email=user.email,
            name=student.name if student else label, branch=student.branch if student else None,
            headers={"Authorization": "Bearer " + token})

    def setUp(self):
        self.a, self.b = self.accounts
        self.headers = self.a["admin"]["headers"]
        self.job = self.new_job(self.a)
        self.other_job = self.new_job(self.b)
        self.payload = dict(job_id=self.job, audience="applicants", branch=None, kind="update",
            title="Local drive update", body="Local test update: please review the recorded interview requirements.")
        # Ignored local rehearsal metadata; these credentials belong only to
        # explicitly controlled localhost fixture accounts, never live users.
        fixture_path = Path(__file__).resolve().parents[2] / ".local/announcements-preview.json"
        fixture_path.write_text(json.dumps(dict(college_id=self.a["college"], job_id=self.job,
            branch=self.branch, admin_email=self.a["admin"]["email"],
            student_email=self.a["students"]["p0"]["email"], password=self.fixture_password), indent=2), encoding="utf-8")

    def new_job(self, account, recruiter="recruiter"):
        body = JobInput(title=f"Local announcement drive {self.suffix}", ctc=6, min_cgpa=5,
            eligible_branches=[self.branch, self.other_branch],
            required_skills=[dict(skill_name="python", min_proficiency=60)]).model_dump()
        with tenant_session(account["college"]) as session:
            row = Job(college_id=account["college"], company_id=account[recruiter]["company_id"], **body)
            session.add(row); session.flush()
            return row.id

    def application(self, label, status="submitted", account=None, job=None):
        account = account or self.a
        with tenant_session(account["college"]) as session:
            student = session.scalar(select(Student).where(Student.college_id == account["college"],
                Student.id == account["students"][label]["student_id"]))
            drive, company = session.execute(select(Job, Company).join(Company,
                (Company.id == Job.company_id) & (Company.college_id == Job.college_id)).where(
                    Job.college_id == account["college"], Company.college_id == account["college"],
                    Job.id == (job or self.job))).one()
            row = Application(college_id=account["college"], student_id=student.id, job_id=drive.id,
                status=status, evidence_snapshot=application_fixture_snapshot(session, student, drive, company))
            session.add(row); session.flush()
            return row.id

    def saved_match(self, label, eligible=True, override=None):
        with tenant_session(self.a["college"]) as session:
            row = Match(college_id=self.a["college"], job_id=self.job,
                student_id=self.a["students"][label]["student_id"], match_score=80 if eligible else 20,
                factor_breakdown=[], missing_requirements=[], skill_gaps=[], eligible=eligible,
                explanation="Controlled saved-match fixture for audience selection.",
                next_step="Human review required.", methodology="Local fixture, not a measured engine result.",
                override_action=override)
            session.add(row); session.flush()
            return row.id

    def booking(self, label, status="scheduled", round_number=1, past=False, person=None):
        person = person or self.a["students"][label]
        start = datetime.now(timezone.utc) - timedelta(days=2) if past else datetime(2055, 1, 1, tzinfo=timezone.utc)
        with tenant_session(self.a["college"]) as session:
            row = Interview(college_id=self.a["college"], job_id=self.job, student_id=person["student_id"],
                scheduled_time=start, end_time=start + timedelta(minutes=30), venue="local announcement room",
                panel_id="local announcement panel", status=status, round_number=round_number,
                round_name="Local test round")
            session.add(row); session.flush()
            return row.id

    def preview(self, payload=None, account=None):
        response = self.client.post("/admin/announcements/preview", headers=(account or self.a)["admin"]["headers"],
            json=payload or self.payload)
        self.assertEqual(response.status_code, 200, response.text)
        value = response.json()
        self.assertLessEqual(len(value["sample"]), 10)
        self.assertRegex(value["preview_hash"], r"^[0-9a-f]{64}$")
        self.assertTrue(value["explanation"])
        return value

    def publish(self, payload=None, account=None, preview=None, key=None):
        payload = payload or self.payload
        preview = preview or self.preview(payload, account)
        body = {**payload, "preview_hash": preview["preview_hash"], "idempotency_key": key or str(uuid.uuid4())}
        response = self.client.post("/admin/announcements", headers=(account or self.a)["admin"]["headers"], json=body)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertTrue(response.json()["explanation"])
        return response.json(), body

    def recipient_rows(self, identity, account=None, page_size=10):
        headers = (account or self.a)["admin"]["headers"]
        first = self.client.get(f"/admin/announcements/{identity}/recipients?limit={page_size}", headers=headers)
        self.assertEqual(first.status_code, 200, first.text)
        total = first.json()["total"]
        rows = first.json()["items"]
        for offset in range(page_size, total, page_size):
            page = self.client.get(f"/admin/announcements/{identity}/recipients?limit={page_size}&offset={offset}", headers=headers)
            self.assertEqual(page.status_code, 200, page.text)
            self.assertEqual(page.json()["total"], total)
            rows += page.json()["items"]
        self.assertEqual(len(rows), total)
        self.assertEqual(len({r["student_id"] for r in rows}), total)
        return rows

    def change(self, model, identity, **values):
        college = self.a["college"]
        with tenant_session(college) as session:
            row = session.scalar(select(model).where(model.college_id == college, model.id == identity))
            before = {key: getattr(row, key) for key in values}
            session.execute(update(model).where(model.college_id == college, model.id == identity).values(**values))
        def restore():
            with tenant_session(college) as session:
                session.execute(update(model).where(model.college_id == college, model.id == identity).values(**before))
        self.addCleanup(restore)

    def test_options_include_only_approved_college_drives_and_student_branches(self):
        pending_job = self.new_job(self.a, "pending_recruiter")
        result = self.client.get("/admin/announcements/options", headers=self.headers)
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()
        jobs = {row["id"] for row in data["jobs"]}
        self.assertIn(self.job, jobs)
        self.assertNotIn(self.other_job, jobs)
        self.assertNotIn(pending_job, jobs)
        self.assertIn(self.branch, data["branches"])
        self.assertIn(self.other_branch, data["branches"])
        self.assertTrue(data["explanation"])

    def test_college_students_are_approved_current_students_with_branch_filter(self):
        payload = {**self.payload, "audience": "college_students", "branch": "  " + self.branch.lower().replace(" ", "   ") + "  "}
        result = self.preview(payload)
        self.assertEqual(result["branch"], self.branch)
        self.assertEqual(result["recipient_count"], 12)
        self.assertEqual(len(result["sample"]), 10)
        published, _ = self.publish(payload, preview=result)
        expected = {self.a["students"]["p" + str(i)]["student_id"] for i in range(12)}
        self.assertEqual({r["student_id"] for r in self.recipient_rows(published["id"])}, expected)
        other = self.preview({**payload, "branch": self.other_branch})
        self.assertEqual(other["recipient_count"], 1)
        self.assertEqual(other["sample"][0]["student_id"], self.a["students"]["other"]["student_id"])

    def test_applicants_include_active_states_and_exclude_unadmitted_users(self):
        for label, status in (("p0", "submitted"), ("p1", "under_review"), ("p2", "shortlisted"),
                ("p3", "withdrawn"), ("p4", "rejected"), ("unverified", "shortlisted"),
                ("pending", "submitted"), ("rejected", "under_review")):
            self.application(label, status)
        result = self.preview()
        self.assertEqual(result["recipient_count"], 3)
        self.assertEqual({r["student_id"] for r in result["sample"]},
            {self.a["students"][label]["student_id"] for label in ("p0", "p1", "p2")})

    def test_shortlisted_sources_apply_application_and_override_vetoes(self):
        self.application("p0", "shortlisted")
        self.saved_match("p1")
        self.saved_match("p2", eligible=False, override="promote")
        self.application("p3", "shortlisted"); self.saved_match("p3", override="reject")
        self.application("p4", "withdrawn"); self.saved_match("p4")
        self.application("p5", "rejected"); self.saved_match("p5", override="promote")
        self.application("p6", "submitted"); self.saved_match("p6", eligible=False, override="promote")
        self.application("p7", "under_review")
        self.saved_match("p8", eligible=False)
        self.saved_match("unverified"); self.application("pending", "shortlisted")
        result = self.preview({**self.payload, "audience": "shortlisted"})
        self.assertEqual(result["recipient_count"], 4)
        self.assertEqual({r["student_id"] for r in result["sample"]},
            {self.a["students"][label]["student_id"] for label in ("p0", "p1", "p2", "p6")})

    def test_scheduled_audience_deduplicates_rounds_and_includes_past_unclosed_booking(self):
        self.booking("p0", past=True)
        self.booking("p0", round_number=2)
        self.booking("p1", status="cancelled")
        self.booking("p2", status="completed")
        self.booking("unverified")
        self.booking(None, person=self.a["admin"])
        with tenant_session(self.a["college"]) as session:
            start = datetime(2055, 2, 1, tzinfo=timezone.utc)
            session.add(Schedule(college_id=self.a["college"], job_id=self.job,
                student_id=self.a["students"]["p3"]["student_id"], requested_time=start,
                scheduled_time=start, end_time=start + timedelta(minutes=30), venue="local room", panel_id="local panel",
                status="pending", conflicts=[], explanation="Controlled pending proposal fixture.", created_by=self.a["admin"]["user_id"]))
        result = self.preview({**self.payload, "audience": "scheduled"})
        self.assertEqual(result["recipient_count"], 1)
        self.assertEqual(result["sample"][0]["student_id"], self.a["students"]["p0"]["student_id"])

    def test_stale_preview_detects_changes_outside_the_displayed_sample(self):
        payload = {**self.payload, "audience": "college_students", "branch": self.branch}
        preview = self.preview(payload)
        sampled = {r["student_id"] for r in preview["sample"]}
        person = next(s for label, s in self.a["students"].items() if label.startswith("p") and label[1:].isdigit() and s["student_id"] not in sampled)
        self.change(Student, person["student_id"], branch=self.other_branch)
        key = str(uuid.uuid4())
        response = self.client.post("/admin/announcements", headers=self.headers,
            json={**payload, "preview_hash": preview["preview_hash"], "idempotency_key": key})
        self.assertEqual(response.status_code, 409, response.text)
        with tenant_session(self.a["college"]) as session:
            self.assertIsNone(session.scalar(select(DriveAnnouncement).where(DriveAnnouncement.college_id == self.a["college"], DriveAnnouncement.idempotency_key == key)))

    def test_content_drive_company_and_recipient_metadata_remain_frozen(self):
        application = self.application("p0")
        published, request = self.publish()
        person = self.a["students"]["p0"]
        self.change(Student, person["student_id"], name="Changed local profile", branch=self.other_branch)
        self.change(Job, self.job, title="Changed local drive")
        self.change(Company, self.a["recruiter"]["company_id"], name="Changed local company")
        self.change(Application, application, status="withdrawn")
        row = self.recipient_rows(published["id"])[0]
        self.assertEqual((row["name"], row["branch"]), (person["name"], person["branch"]))
        replay = self.client.post("/admin/announcements", headers=self.headers, json=request)
        self.assertEqual(replay.status_code, 201, replay.text)
        self.assertEqual(replay.json()["id"], published["id"])
        self.assertEqual(replay.json()["job_title"], published["job_title"])
        self.assertEqual(replay.json()["company_name"], published["company_name"])
        self.assertEqual((replay.json()["title"], replay.json()["body"]), (self.payload["title"], self.payload["body"]))
        self.assertEqual(replay.json()["recipient_count"], 1)

    def test_concurrent_idempotent_publication_and_changed_payload_rejection(self):
        self.application("p0")
        preview = self.preview()
        request = {**self.payload, "preview_hash": preview["preview_hash"], "idempotency_key": str(uuid.uuid4())}
        def send(_):
            return self.client.post("/admin/announcements", headers=self.headers, json=request)
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(send, range(2)))
        self.assertEqual([r.status_code for r in responses], [201, 201])
        self.assertEqual(responses[0].json()["id"], responses[1].json()["id"])
        identity = responses[0].json()["id"]
        rows = self.recipient_rows(identity)
        self.assertEqual(len(rows), 1)
        conflict = self.client.post("/admin/announcements", headers=self.headers,
            json={**request, "body": "Different local publication content with the same request key."})
        self.assertEqual(conflict.status_code, 409, conflict.text)
        with tenant_session(self.a["college"]) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(DriveAnnouncement).where(
                DriveAnnouncement.college_id == self.a["college"], DriveAnnouncement.idempotency_key == request["idempotency_key"])), 1)
            recipient = session.scalar(select(AnnouncementRecipient).where(AnnouncementRecipient.college_id == self.a["college"], AnnouncementRecipient.announcement_id == identity))
            self.assertEqual(session.scalar(select(func.count()).select_from(Notification).where(Notification.college_id == self.a["college"],
                Notification.recipient_user_id == recipient.recipient_user_id, Notification.event_key == recipient.event_key)), 1)

    def test_recipient_pagination_read_ownership_and_read_count_use_notification_state(self):
        payload = {**self.payload, "audience": "college_students", "branch": self.branch, "kind": "reminder"}
        published, _ = self.publish(payload)
        self.assertEqual((published["recipient_count"], published["read_count"]), (12, 0))
        rows = self.recipient_rows(published["id"])
        person = self.a["students"]["p0"]
        recipient = next(r for r in rows if r["student_id"] == person["student_id"])
        route = f"/notifications/{recipient['notification_id']}/read"
        self.assertEqual(self.client.put(route, headers=self.a["students"]["p1"]["headers"]).status_code, 404)
        self.assertEqual(self.client.put(route, headers=self.b["students"]["p0"]["headers"]).status_code, 404)
        self.assertEqual(self.client.put(route, headers=self.headers).status_code, 404)
        first = self.client.put(route, headers=person["headers"])
        second = self.client.put(route, headers=person["headers"])
        self.assertEqual((first.status_code, second.status_code), (200, 200))
        self.assertEqual(datetime.fromisoformat(first.json()["read_at"].replace("Z", "+00:00")),
            datetime.fromisoformat(second.json()["read_at"].replace("Z", "+00:00")))
        feed = self.client.get("/notifications", headers=person["headers"])
        self.assertEqual(feed.status_code, 200, feed.text)
        notice = next(n for n in feed.json()["notifications"] if n["id"] == recipient["notification_id"])
        self.assertEqual(notice["kind"], "drive_reminder")
        self.assertEqual(notice["title"], payload["title"])
        self.assertTrue(notice["body"].endswith(payload["body"]))
        self.assertIn(published["job_title"], notice["body"])
        self.assertIn(published["company_name"], notice["body"])
        self.assertEqual(notice["delivery"], "in_app")
        after = self.recipient_rows(published["id"])
        self.assertEqual(sum(r["read_at"] is not None for r in after), 1)
        listing = self.client.get("/admin/announcements", headers=self.headers)
        self.assertEqual(listing.status_code, 200, listing.text)
        recorded = next(r for r in listing.json()["items"] if r["id"] == published["id"])
        self.assertEqual((recorded["recipient_count"], recorded["read_count"]), (12, 1))

    def test_partial_notification_failure_rolls_back_publication_and_all_recipients(self):
        self.application("p0"); self.application("p1")
        preview = self.preview()
        key = str(uuid.uuid4())
        ids = [self.a["students"][label]["user_id"] for label in ("p0", "p1")]
        with tenant_session(self.a["college"]) as session:
            before = session.scalar(select(func.count()).select_from(Notification).where(Notification.college_id == self.a["college"], Notification.recipient_user_id.in_(ids)))
        original = announcements.persist_notifications
        def fail_after_one(session, college, announcement, rows):
            original(session, college, announcement, rows[:1])
            raise HTTPException(503, "Controlled local notification failure.")
        with patch.object(announcements, "persist_notifications", side_effect=fail_after_one):
            response = self.client.post("/admin/announcements", headers=self.headers,
                json={**self.payload, "preview_hash": preview["preview_hash"], "idempotency_key": key})
        self.assertEqual(response.status_code, 503, response.text)
        with tenant_session(self.a["college"]) as session:
            self.assertIsNone(session.scalar(select(DriveAnnouncement).where(DriveAnnouncement.college_id == self.a["college"], DriveAnnouncement.idempotency_key == key)))
            after = session.scalar(select(func.count()).select_from(Notification).where(Notification.college_id == self.a["college"], Notification.recipient_user_id.in_(ids)))
            self.assertEqual(after, before)
        # The failed key has no published record and can be deliberately retried.
        published, _ = self.publish(preview=preview, key=key)
        self.assertEqual(published["recipient_count"], 2)

    def test_role_and_tenant_guards_and_announcement_list_pagination(self):
        self.application("p0")
        first, request = self.publish()
        second, _ = self.publish({**self.payload, "title": "Another local update"})
        for headers, expected in (({}, 401), (self.a["students"]["p0"]["headers"], 403), (self.a["recruiter"]["headers"], 403)):
            for path in ("/admin/announcements", "/admin/announcements/options", f"/admin/announcements/{first['id']}/recipients"):
                self.assertEqual(self.client.get(path, headers=headers).status_code, expected)
            self.assertEqual(self.client.post("/admin/announcements/preview", headers=headers, json=self.payload).status_code, expected)
            self.assertEqual(self.client.post("/admin/announcements", headers=headers, json=request).status_code, expected)
        self.assertEqual(self.client.get(f"/admin/announcements/{first['id']}/recipients", headers=self.b["admin"]["headers"]).status_code, 404)
        self.assertEqual(self.client.post("/admin/announcements/preview", headers=self.headers,
            json={**self.payload, "job_id": self.other_job}).status_code, 404)
        for offset, expected in ((0, second["id"]), (1, first["id"])):
            page = self.client.get(f"/admin/announcements?limit=1&offset={offset}", headers=self.headers)
            self.assertEqual(page.status_code, 200, page.text)
            self.assertEqual([r["id"] for r in page.json()["items"]], [expected])

    def test_drive_recruiter_approval_is_rechecked_at_publication(self):
        self.application("p0")
        preview = self.preview()
        with tenant_session(self.a["college"]) as session:
            access_id = session.scalar(select(AccountAccess.id).where(AccountAccess.college_id == self.a["college"],
                AccountAccess.user_id == self.a["recruiter"]["user_id"]))
        self.change(AccountAccess, access_id, approval_status="rejected")
        response = self.client.post("/admin/announcements", headers=self.headers,
            json={**self.payload, "preview_hash": preview["preview_hash"], "idempotency_key": str(uuid.uuid4())})
        self.assertEqual(response.status_code, 404, response.text)
        options = self.client.get("/admin/announcements/options", headers=self.headers).json()
        self.assertNotIn(self.job, [j["id"] for j in options["jobs"]])

    def test_empty_audience_and_invalid_contracts_never_publish(self):
        preview = self.preview()
        self.assertEqual(preview["recipient_count"], 0)
        empty = self.client.post("/admin/announcements", headers=self.headers,
            json={**self.payload, "preview_hash": preview["preview_hash"], "idempotency_key": str(uuid.uuid4())})
        self.assertEqual(empty.status_code, 409, empty.text)
        for changes in (dict(audience="everyone"), dict(kind="email"), dict(title="x"), dict(body="short"),
                dict(branch=" "), dict(job_id=0), dict(title="x" * 161), dict(body="x" * 4001)):
            with self.subTest(changes=changes):
                response = self.client.post("/admin/announcements/preview", headers=self.headers, json={**self.payload, **changes})
                self.assertEqual(response.status_code, 422, response.text)
        self.application("p0")
        valid = {**self.payload, "preview_hash": self.preview()["preview_hash"], "idempotency_key": str(uuid.uuid4())}
        for changes in (dict(preview_hash="not-a-hash"), dict(idempotency_key="not-a-uuid")):
            self.assertEqual(self.client.post("/admin/announcements", headers=self.headers, json={**valid, **changes}).status_code, 422)

    def test_legacy_demo_admin_retaining_student_row_is_never_targeted(self):
        with tenant_session(1) as session:
            admin = self.make_person(session, 1, "demo-admin", "admin", profile=True)
            recruiter = self.make_person(session, 1, "demo-recruiter", "recruiter")
            company = Company(college_id=1, recruiter_user_id=recruiter["user_id"], name="Local archived announcement fixture", industry="Testing")
            session.add(company); session.flush()
            job = Job(college_id=1, company_id=company.id, **JobInput(title="Local archive role check", ctc=6, min_cgpa=5,
                eligible_branches=[self.branch], required_skills=[dict(skill_name="python", min_proficiency=60)]).model_dump())
            session.add(job); session.flush(); identity = job.id
            retained_company = Company(college_id=1, recruiter_user_id=admin["user_id"], name="Local retained admin company", industry="Testing")
            session.add(retained_company); session.flush()
            retained_job = Job(college_id=1, company_id=retained_company.id, **JobInput(title="Local retained admin drive", ctc=6, min_cgpa=5,
                eligible_branches=[self.branch], required_skills=[dict(skill_name="python", min_proficiency=60)]).model_dump())
            session.add(retained_job); session.flush(); retained_identity = retained_job.id
        accounts = json.loads(os.environ["ADMIN_ACCOUNTS"]) + [dict(email=admin["email"], college_id=1)]
        with patch.dict(os.environ, {"ADMIN_ACCOUNTS": json.dumps(accounts)}):
            response = self.client.post("/admin/announcements/preview", headers=admin["headers"],
                json={**self.payload, "job_id": identity, "audience": "college_students", "branch": self.branch})
            options = self.client.get("/admin/announcements/options", headers=admin["headers"])
            invalid_drive = self.client.post("/admin/announcements/preview", headers=admin["headers"],
                json={**self.payload, "job_id": retained_identity, "audience": "college_students", "branch": self.branch})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["recipient_count"], 0)
        self.assertEqual(options.status_code, 200, options.text)
        self.assertIn(identity, [j["id"] for j in options.json()["jobs"]])
        self.assertNotIn(retained_identity, [j["id"] for j in options.json()["jobs"]])
        self.assertEqual(invalid_drive.status_code, 404, invalid_drive.text)

    def test_new_tables_force_rls_for_contextless_and_cross_college_reads_writes(self):
        self.application("p0")
        own, _ = self.publish()
        self.application("p0", account=self.b, job=self.other_job)
        other, _ = self.publish({**self.payload, "job_id": self.other_job}, account=self.b)
        for model in (DriveAnnouncement, AnnouncementRecipient):
            with self.subTest(table=model.__tablename__), tenant_session(self.a["college"]) as session:
                # Omit application filters only to exercise database isolation.
                rows = session.scalars(select(model)).all()
                self.assertTrue(rows)
                self.assertTrue(all(r.college_id == self.a["college"] for r in rows))
                source = next(r for r in rows if (r.id == own["id"] if model is DriveAnnouncement else r.announcement_id == own["id"]))
                values = {c.name: getattr(source, c.name) for c in model.__table__.columns if c.name != "id"}
                identity = source.id
            with SessionLocal() as session:
                self.assertEqual(session.scalars(select(model)).all(), [])
            with tenant_session(self.b["college"]) as session:
                visible = session.scalars(select(model)).all()
                self.assertTrue(visible)
                self.assertTrue(all(r.college_id == self.b["college"] for r in visible))
                self.assertIsNone(session.scalar(select(model).where(model.id == identity)))
            with self.assertRaises(DBAPIError) as blocked:
                with tenant_session(self.b["college"]) as session:
                    session.execute(insert(model).values(**values))
            self.assertIn("row-level security", str(blocked.exception).lower())
            with self.assertRaises(DBAPIError) as blocked:
                with tenant_session(self.a["college"]) as session:
                    session.execute(update(model).where(model.college_id == self.a["college"], model.id == identity).values(college_id=self.b["college"]))
            self.assertIn("row-level security", str(blocked.exception).lower())
        self.assertEqual(self.client.get(f"/admin/announcements/{other['id']}/recipients", headers=self.headers).status_code, 404)
        with engine.connect() as connection:
            policies = connection.execute(text("SELECT tablename,policyname,qual,with_check FROM pg_policies WHERE schemaname=current_schema() AND tablename IN ('drive_announcements','announcement_recipients')")).all()
            self.assertEqual(len(policies), 2)
            self.assertTrue(all(p.policyname == "college_isolation" and "college_id" in p.qual and "college_id" in p.with_check for p in policies))
            tables = connection.execute(text("SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('drive_announcements','announcement_recipients')")).all()
            self.assertEqual(len(tables), 2)
            self.assertTrue(all(t.relrowsecurity and t.relforcerowsecurity for t in tables))


if __name__ == "__main__":
    unittest.main()
