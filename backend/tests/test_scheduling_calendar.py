"""Deterministic calendar checks and guarded real-PostgreSQL scheduling tests.

Only local, explicitly approved test databases are used. Test admission is a
controlled fixture, not a claim of live email delivery or institutional review.
"""
import json
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as Obj
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError

from database import SessionLocal, engine, initialize_schema, tenant_session
from engines.scheduler import propose_slot
from main import app
from models import AccountAccess, CalendarConstraint, CalendarSettings, Interview, User
from schemas import ScheduleInput


def moment(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def settings(**changes):
    values = dict(enabled=False, timezone="Asia/Kolkata", weekdays=[0, 1, 2, 3, 4],
        day_start="09:00", day_end="17:00", require_student_availability=False,
        require_panel_availability=False)
    return Obj(**{**values, **changes})


def constraint(identity, start, end, kind="unavailable", scope="student", **changes):
    values = dict(id=identity, starts_at=moment(start), ends_at=moment(end), kind=kind,
        scope=scope, student_id=1 if scope == "student" else None,
        resource_name="panel a" if scope == "panel" else "CSE" if scope == "branch" else None,
        status="active", label="Local calendar fixture")
    return Obj(**{**values, **changes})


class CalendarRuleTests(unittest.TestCase):
    def slot(self, value="2035-01-01T10:00:00Z", **changes):
        return ScheduleInput(**{**dict(job_id=1, student_id=1, scheduled_time=moment(value),
            duration_minutes=30, venue="Hall A", panel_id="Panel A"), **changes})

    def test_default_calendar_does_not_invent_availability(self):
        slot = self.slot()
        result = propose_slot(slot, [])
        self.assertEqual(result.proposed_time, slot.scheduled_time)
        self.assertEqual(result.calendar_conflicts, [])
        self.assertTrue(result.requires_approval)
        self.assertTrue(result.explanation)
        enforced = propose_slot(slot, [], settings(require_student_availability=True))
        self.assertIsNone(enforced.proposed_time)
        self.assertTrue(enforced.calendar_conflicts)
        self.assertIn("availability", enforced.explanation.lower())

    def test_student_and_panel_windows_intersect_for_whole_duration(self):
        rows = [constraint(1, "2035-01-01T10:00:00Z", "2035-01-01T12:00:00Z", "available"),
            constraint(2, "2035-01-01T11:00:00Z", "2035-01-01T12:00:00Z", "available", "panel")]
        result = propose_slot(self.slot(), [], settings(), rows, "CSE")
        self.assertEqual(result.proposed_time, moment("2035-01-01T11:00:00Z"))
        self.assertEqual(result.proposed_end_time, moment("2035-01-01T11:30:00Z"))
        self.assertTrue(result.calendar_conflicts)
        self.assertTrue(all(c.explanation for c in result.calendar_conflicts))

    def test_short_window_is_skipped_and_touching_windows_are_joined(self):
        rows = [constraint(1, "2035-01-01T10:00:00Z", "2035-01-01T10:20:00Z", "available"),
            constraint(2, "2035-01-01T11:00:00Z", "2035-01-01T11:20:00Z", "available"),
            constraint(3, "2035-01-01T11:20:00Z", "2035-01-01T11:40:00Z", "available")]
        result = propose_slot(self.slot(), [], settings(), rows)
        self.assertEqual(result.proposed_time, moment("2035-01-01T11:00:00Z"))
        self.assertEqual(result.proposed_end_time, moment("2035-01-01T11:30:00Z"))

    def test_exam_branch_campus_and_cancelled_windows(self):
        rows = [constraint(1, "2035-01-01T10:00:00Z", "2035-01-01T10:30:00Z", "exam", "branch"),
            constraint(2, "2035-01-01T10:30:00Z", "2035-01-01T11:00:00Z", "exam", "campus"),
            constraint(3, "2035-01-01T11:00:00Z", "2035-01-01T13:00:00Z", status="cancelled"),
            constraint(4, "2035-01-01T10:00:00Z", "2035-01-01T14:00:00Z", "exam", "branch", resource_name="ECE")]
        result = propose_slot(self.slot(), [], settings(), rows, "CSE")
        self.assertEqual(result.proposed_time, moment("2035-01-01T11:00:00Z"))
        self.assertEqual({c.constraint_id for c in result.calendar_conflicts if c.constraint_id}, {1, 2})
        self.assertEqual(propose_slot(self.slot(), [], settings(), rows[:1], "ECE").proposed_time,
            self.slot().scheduled_time)

    def test_known_windows_outside_horizon_are_not_bypassed(self):
        rows = [constraint(1, "2035-01-10T10:00:00Z", "2035-01-10T12:00:00Z", "available")]
        result = propose_slot(self.slot(), [], settings(), rows)
        self.assertIsNone(result.proposed_time)
        self.assertTrue(result.calendar_conflicts)
        blocked = [constraint(2, "2035-01-01T00:00:00Z", "2035-01-09T00:00:00Z", "exam", "campus")]
        self.assertIsNone(propose_slot(self.slot(), [], settings(), blocked).proposed_time)

    def test_student_panel_unavailability_and_full_search_horizon(self):
        rows = [constraint(1, "2035-01-01T10:00:00Z", "2035-01-01T12:00:00Z", "available"),
            constraint(2, "2035-01-01T10:00:00Z", "2035-01-01T12:00:00Z", "available", "panel"),
            constraint(3, "2035-01-01T10:00:00Z", "2035-01-01T10:30:00Z"),
            constraint(4, "2035-01-01T10:30:00Z", "2035-01-01T11:00:00Z", "unavailable", "panel")]
        result = propose_slot(self.slot(), [], settings(), rows)
        self.assertEqual(result.proposed_time, moment("2035-01-01T11:00:00Z"))
        self.assertEqual({c.constraint_id for c in result.calendar_conflicts if c.constraint_id}, {3, 4})
        # A start inside seven days is insufficient when the end crosses the horizon.
        edge = [constraint(5, "2035-01-01T10:00:00Z", "2035-01-08T09:45:00Z", "exam", "campus")]
        self.assertIsNone(propose_slot(self.slot(), [], settings(), edge).proposed_time)

    def test_recorded_interview_rounds_have_temporal_order(self):
        earlier = Obj(id=7, job_id=1, student_id=1, venue="other", panel_id="other",
            status="scheduled", round_number=1, scheduled_time=moment("2035-01-01T10:00:00Z"),
            end_time=moment("2035-01-01T10:30:00Z"))
        result = propose_slot(self.slot(round_number=2, round_name="Technical"), [earlier])
        self.assertEqual(result.proposed_time, earlier.end_time)
        self.assertIn("round_order", [c.kind for c in result.calendar_conflicts])
        later = Obj(id=8, job_id=1, student_id=1, venue="other", panel_id="other",
            status="scheduled", round_number=3, scheduled_time=moment("2035-01-01T11:15:00Z"),
            end_time=moment("2035-01-01T11:45:00Z"))
        blocked = propose_slot(self.slot("2035-01-01T11:00:00Z", round_number=2), [later])
        self.assertIsNone(blocked.proposed_time)
        self.assertIn("round_order", [c.kind for c in blocked.calendar_conflicts])

    def test_working_hours_use_college_timezone_full_fit_and_weekdays(self):
        # 2035-01-05 is Friday; 17:45 IST cannot fit a 30-minute interview.
        result = propose_slot(self.slot("2035-01-05T17:45:00+05:30"), [], settings(enabled=True))
        self.assertEqual(result.proposed_time, moment("2035-01-08T09:00:00+05:30"))
        self.assertTrue(result.calendar_conflicts)
        # UTC Sunday evening is already Monday locally; dates must be localized.
        midnight = propose_slot(self.slot("2035-01-07T19:30:00Z"), [], settings(enabled=True))
        self.assertEqual(midnight.proposed_time, moment("2035-01-08T03:30:00Z"))
        adjacent = propose_slot(self.slot("2035-01-08T16:30:00+05:30"), [], settings(enabled=True))
        self.assertEqual(adjacent.proposed_end_time, moment("2035-01-08T17:00:00+05:30"))

    def test_dst_daily_hours_use_current_offset_not_fixed_offset(self):
        campus = settings(enabled=True, timezone="America/New_York", weekdays=[6])
        spring = propose_slot(self.slot("2035-03-11T12:00:00Z"), [], campus)
        fall = propose_slot(self.slot("2035-11-04T13:00:00Z"), [], campus)
        self.assertEqual(spring.proposed_time, moment("2035-03-11T13:00:00Z"))
        self.assertEqual(fall.proposed_time, moment("2035-11-04T14:00:00Z"))

    def test_positive_windows_and_booking_blockers_are_rechecked_together(self):
        rows = [constraint(1, "2035-01-01T10:00:00Z", "2035-01-01T12:00:00Z", "available"),
            constraint(2, "2035-01-01T11:00:00Z", "2035-01-01T12:00:00Z", "available", "panel")]
        booking = Obj(id=7, job_id=2, student_id=8, venue="hall a", panel_id="other",
            status="scheduled", scheduled_time=moment("2035-01-01T11:00:00Z"),
            end_time=moment("2035-01-01T11:30:00Z"))
        result = propose_slot(self.slot(), [booking], settings(), rows)
        self.assertEqual(result.proposed_time, moment("2035-01-01T11:30:00Z"))
        self.assertEqual([c.interview_id for c in result.conflicts], [7])
        self.assertTrue(result.calendar_conflicts)
        self.assertEqual(self.slot().scheduled_time, moment("2035-01-01T10:00:00Z"))


class CalendarIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine is None or engine.url.host not in ("localhost", "127.0.0.1"):
            raise RuntimeError("Explicit localhost test database required.")
        initialize_schema()
        cls.client = TestClient(app)
        cls.suffix = uuid.uuid4().hex[:12]
        cls.accounts = []
        cls.start = moment("2045-01-01T10:00:00Z") + timedelta(days=int(cls.suffix[:4], 16))
        for college in (10220, 10221):
            account = {"college": college}
            for role in ("admin", "student", "recruiter"):
                credentials = dict(email=f"calendar-{role}-{cls.suffix}-{college}@test.invalid",
                    password="Local-calendar-test-2026", college_id=college)
                body = {**credentials, "company": {"name": "Local calendar company", "industry": "Testing"}} if role == "recruiter" else {**credentials, "name": "Local calendar fixture"}
                created = cls.client.post("/auth/recruiter/signup" if role == "recruiter" else "/auth/signup", json=body)
                assert created.status_code == 201, created.text
                value = created.json()
                with tenant_session(college) as session:
                    if role == "admin":
                        session.execute(update(User).where(User.college_id == college,
                            User.id == value["user"]["user_id"]).values(role="admin"))
                    session.add(AccountAccess(college_id=college, user_id=value["user"]["user_id"],
                        email_verified_at=datetime.now(timezone.utc), approval_status="approved"))
                account[role] = {**value, "credentials": credentials}
            cls.accounts.append(account)
        cls.allowlist = patch.dict(os.environ, {"ADMIN_ACCOUNTS": json.dumps([
            dict(email=a["admin"]["user"]["email"], college_id=a["college"]) for a in cls.accounts])})
        cls.allowlist.start()
        for a in cls.accounts:
            for role in ("admin", "student", "recruiter"):
                login = cls.client.post("/auth/login", json=a[role]["credentials"])
                assert login.status_code == 200, login.text
                a[role]["headers"] = {"Authorization": "Bearer " + login.json()["access_token"]}
            sid = a["student"]["user"]["student_id"]
            profile = cls.client.put(f"/students/{sid}", headers=a["student"]["headers"], json=dict(
                name="Local calendar fixture", branch="CSE", cgpa=8,
                skills=[dict(skill_name="python", proficiency=90)]))
            assert profile.status_code == 200, profile.text

    @classmethod
    def reset_calendars(cls):
        for a in cls.accounts:
            actors = [a[role]["user"]["user_id"] for role in ("admin", "student", "recruiter")]
            with tenant_session(a["college"]) as session:
                session.execute(update(CalendarConstraint).where(CalendarConstraint.college_id == a["college"],
                    CalendarConstraint.created_by.in_(actors), CalendarConstraint.status == "active").values(
                        status="cancelled", version=CalendarConstraint.version + 1))
            current = cls.client.get("/admin/calendar/settings", headers=a["admin"]["headers"])
            assert current.status_code == 200, current.text
            result = cls.client.put("/admin/calendar/settings", headers=a["admin"]["headers"], json=dict(
                version=current.json()["version"], reason="Restore local calendar fixture defaults", enabled=False,
                timezone="Asia/Kolkata", weekdays=[0, 1, 2, 3, 4], day_start="09:00", day_end="17:00",
                require_student_availability=False, require_panel_availability=False))
            assert result.status_code == 200, result.text

    @classmethod
    def tearDownClass(cls):
        try:
            cls.reset_calendars()
        finally:
            cls.allowlist.stop()

    def setUp(self):
        self.reset_calendars()
        self.a, self.b = self.accounts
        self.headers = self.a["admin"]["headers"]
        self.sid = self.a["student"]["user"]["student_id"]
        self.at = self.start + timedelta(days=list(sorted(n for n in dir(self) if n.startswith("test_"))).index(self._testMethodName) * 10)
        # A separate drive prevents recorded round order in one test constraining
        # later tests for the same fixture student. Existing bookings stay intact.
        drive = self.client.post("/recruiters/jobs", headers=self.a["recruiter"]["headers"], json=dict(
            title="Local calendar fixture drive", ctc=6, min_cgpa=5, eligible_branches=["CSE"],
            required_skills=[dict(skill_name="python", min_proficiency=60)]))
        self.assertEqual(drive.status_code, 201, drive.text)
        self.job_id = drive.json()["id"]
        application = self.client.post(f"/students/{self.sid}/applications", headers=self.a["student"]["headers"], json=dict(job_id=self.job_id))
        self.assertEqual(application.status_code, 201, application.text)
        row = application.json()
        shortlisted = self.client.post(f"/recruiters/jobs/{self.job_id}/applications/{row['id']}/review",
            headers=self.a["recruiter"]["headers"], json=dict(version=row["version"], status="shortlisted",
                reason="Local calendar fixture shortlist"))
        self.assertEqual(shortlisted.status_code, 200, shortlisted.text)
        self.slot = dict(job_id=self.job_id, student_id=self.sid, scheduled_time=self.at.isoformat(),
            duration_minutes=30, venue="room-" + self.suffix, panel_id="panel-" + self.suffix)

    def tearDown(self):
        self.reset_calendars()

    def admin_constraint(self, **changes):
        body = dict(kind="exam", scope="campus", starts_at=self.at.isoformat(),
            ends_at=(self.at + timedelta(minutes=30)).isoformat(), label="Local calendar fixture",
            reason="Local calendar fixture constraint")
        result = self.client.post("/admin/calendar/constraints", headers=self.headers, json={**body, **changes})
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def setting(self, **changes):
        current = self.client.get("/admin/calendar/settings", headers=self.headers).json()
        body = dict(version=current["version"], reason="Local calendar fixture setting", enabled=False,
            timezone="Asia/Kolkata", weekdays=[0, 1, 2, 3, 4], day_start="09:00", day_end="17:00",
            require_student_availability=False, require_panel_availability=False)
        result = self.client.put("/admin/calendar/settings", headers=self.headers, json={**body, **changes})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def preview(self, **changes):
        result = self.client.post("/admin/schedules/check-conflict", headers=self.headers, json={**self.slot, **changes})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def proposal(self, **changes):
        result = self.client.post("/admin/schedules", headers=self.headers, json={**self.slot, **changes})
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def review(self, row):
        return self.client.post(f"/admin/schedules/{row['id']}/review", headers=self.headers,
            json=dict(version=row["version"], action="approve", reason="Local calendar fixture approval"))

    def test_settings_versions_role_guards_and_auditable_change(self):
        before = self.client.get("/admin/calendar/settings", headers=self.headers).json()
        saved = self.setting(enabled=True, day_start="08:30", day_end="16:30")
        self.assertEqual(saved["version"], before["version"] + 1)
        self.assertTrue(saved["enabled"])
        stale = {k: saved[k] for k in ("enabled", "timezone", "weekdays", "day_start", "day_end",
            "require_student_availability", "require_panel_availability")}
        stale.update(version=before["version"], reason="Local outdated settings write")
        self.assertEqual(self.client.put("/admin/calendar/settings", headers=self.headers, json=stale).status_code, 409)
        self.assertEqual(self.client.get("/admin/calendar/settings", headers=self.a["student"]["headers"]).status_code, 403)
        board = self.client.get("/admin/schedules", headers=self.headers).json()
        self.assertTrue(any(e["reason"] == "Local calendar fixture setting" for e in board["audit"]))

    def test_student_availability_ownership_and_versioned_cancellation(self):
        route = f"/students/{self.sid}/availability"
        payload = dict(kind="available", starts_at=self.at.isoformat(),
            ends_at=(self.at + timedelta(hours=2)).isoformat(), label="Local calendar fixture student window")
        created = self.client.post(route, headers=self.a["student"]["headers"], json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        row = created.json()
        self.assertEqual(row["scope"], "student")
        self.assertEqual(row["student_id"], self.sid)
        self.assertEqual(self.client.get(route, headers=self.b["student"]["headers"]).status_code, 404)
        self.assertEqual(self.client.post(route, headers=self.b["student"]["headers"], json=payload).status_code, 404)
        for forbidden in [{**payload, "kind": "exam"}, {**payload, "scope": "campus"},
                {**payload, "student_id": self.b["student"]["user"]["student_id"]}]:
            self.assertEqual(self.client.post(route, headers=self.a["student"]["headers"], json=forbidden).status_code, 422)
        listed = self.client.get(route + "?limit=1&offset=0", headers=self.a["student"]["headers"])
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([r["id"] for r in listed.json()["items"]], [row["id"]])
        cancel = route + f"/{row['id']}/cancel"
        body = dict(version=row["version"], reason="Local student window cancellation")
        self.assertEqual(self.client.put(cancel, headers=self.b["student"]["headers"], json=body).status_code, 404)
        cancelled = self.client.put(cancel, headers=self.a["student"]["headers"], json=body)
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        self.assertEqual(cancelled.json()["status"], "cancelled")
        self.assertEqual(self.client.put(cancel, headers=self.a["student"]["headers"], json=body).status_code, 409)

    def test_admin_constraints_exam_scope_paging_and_cancel_rechecks(self):
        row = self.admin_constraint(kind="exam", scope="branch", resource_name=" cse ")
        self.assertEqual(row["resource_name"], "CSE")
        result = self.preview()
        self.assertEqual(moment(result["proposed_time"]), self.at + timedelta(minutes=30))
        self.assertIn(row["id"], [c["constraint_id"] for c in result["calendar_conflicts"]])
        self.assertTrue(all(c["explanation"] for c in result["calendar_conflicts"]))
        route = f"/admin/calendar/constraints/{row['id']}/cancel"
        body = dict(version=row["version"], reason="Local exam cancellation fixture")
        self.assertEqual(self.client.put(route, headers=self.b["admin"]["headers"], json=body).status_code, 404)
        self.assertEqual(self.client.put(route, headers=self.headers, json=body).status_code, 200)
        self.assertEqual(self.client.put(route, headers=self.headers, json=body).status_code, 409)
        self.assertEqual(moment(self.preview()["proposed_time"]), self.at)
        page = self.client.get("/admin/calendar/constraints?limit=1&offset=0", headers=self.headers)
        self.assertEqual(page.status_code, 200, page.text)
        self.assertLessEqual(len(page.json()["items"]), 1)
        self.assertEqual(self.client.post("/admin/calendar/constraints", headers=self.a["recruiter"]["headers"], json=body).status_code, 403)

    def test_invalid_calendar_inputs_do_not_create_constraints(self):
        template = dict(kind="exam", scope="campus", starts_at=self.at.isoformat(),
            ends_at=(self.at + timedelta(minutes=30)).isoformat(), label="Local invalid fixture", reason="Local validation fixture")
        invalid = [dict(kind="available", scope="campus"), dict(scope="student", kind="unavailable"),
            dict(scope="panel", kind="unavailable"), dict(scope="branch"), dict(student_id=self.sid),
            dict(ends_at=self.at.isoformat()), dict(starts_at="2045-01-01T10:00:00"),
            dict(scope="campus", resource_name="unexpected")]
        for changes in invalid:
            with self.subTest(changes=changes):
                response = self.client.post("/admin/calendar/constraints", headers=self.headers, json={**template, **changes})
                self.assertEqual(response.status_code, 422, response.text)
        current = self.client.get("/admin/calendar/settings", headers=self.headers).json()
        base = {k: current[k] for k in ("enabled", "timezone", "weekdays", "day_start", "day_end",
            "require_student_availability", "require_panel_availability")}
        base.update(version=current["version"], reason="Local settings validation fixture")
        for changes in [dict(timezone="Not/AZone"), dict(weekdays=[7]), dict(day_start="25:00"),
                dict(day_start="17:00", day_end="09:00"), dict(weekdays=[0, 0]), dict(enabled=True, weekdays=[])]:
            with self.subTest(changes=changes):
                result = self.client.put("/admin/calendar/settings", headers=self.headers, json={**base, **changes})
                self.assertEqual(result.status_code, 422, result.text)
        for changes in [dict(round_number=0), dict(round_number=21), dict(round_name=" ")]:
            self.assertEqual(self.client.post("/admin/schedules/check-conflict", headers=self.headers,
                json={**self.slot, **changes}).status_code, 422)

    def test_approval_rechecks_calendar_and_existing_bookings_remain(self):
        old = self.proposal(scheduled_time=(self.at + timedelta(days=1)).isoformat())
        self.assertEqual(self.review(old).status_code, 200)
        pending = self.proposal()
        self.admin_constraint(kind="exam", scope="campus")
        approval = self.review(pending)
        self.assertEqual(approval.status_code, 409, approval.text)
        revised = self.client.post(f"/admin/schedules/{pending['id']}/recheck", headers=self.headers,
            json=dict(version=pending["version"]))
        self.assertEqual(revised.status_code, 200, revised.text)
        self.assertEqual(moment(revised.json()["scheduled_time"]), self.at + timedelta(minutes=30))
        self.assertTrue(revised.json()["calendar_conflicts"])
        self.assertEqual(self.review(revised.json()).status_code, 200)
        self.admin_constraint(starts_at=(self.at + timedelta(days=1)).isoformat(),
            ends_at=(self.at + timedelta(days=1, hours=1)).isoformat())
        board = self.client.get("/admin/schedules", headers=self.headers).json()
        booking = next(i for i in board["interviews"] if i["schedule_id"] == old["id"])
        self.assertEqual(booking["status"], "scheduled")
        self.assertTrue(any(i["interview_id"] == booking["id"] for i in board["calendar_alerts"]))

    def test_missing_required_windows_fail_then_student_panel_intersection_passes(self):
        self.setting(require_student_availability=True, require_panel_availability=True)
        self.assertIsNone(self.preview()["proposed_time"])
        self.assertEqual(self.client.post("/admin/schedules", headers=self.headers, json=self.slot).status_code, 409)
        self.admin_constraint(kind="available", scope="student", student_id=self.sid,
            ends_at=(self.at + timedelta(hours=2)).isoformat())
        self.assertIsNone(self.preview()["proposed_time"])
        self.admin_constraint(kind="available", scope="panel", resource_name=self.slot["panel_id"],
            starts_at=(self.at + timedelta(hours=1)).isoformat(), ends_at=(self.at + timedelta(hours=2)).isoformat())
        self.assertEqual(moment(self.preview()["proposed_time"]), self.at + timedelta(hours=1))

    def test_concurrent_approvals_stale_versions_and_round_reschedule(self):
        rows = [self.proposal(round_number=2, round_name="Technical") for _ in range(2)]
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(self.review, rows))
        self.assertEqual(sorted(r.status_code for r in responses), [200, 409])
        winner = rows[next(i for i, r in enumerate(responses) if r.status_code == 200)]
        self.assertEqual(self.review(winner).status_code, 409)
        board = self.client.get("/admin/schedules", headers=self.headers).json()
        source = next(i for i in board["interviews"] if i["schedule_id"] == winner["id"])
        self.assertEqual((source["round_number"], source["round_name"]), (2, "Technical"))
        changed_round = self.client.post("/admin/schedules", headers=self.headers, json={**self.slot,
            "round_number": 3, "round_name": "Final", "reschedule_interview_id": source["id"],
            "scheduled_time": (self.at + timedelta(hours=2)).isoformat()})
        self.assertEqual(changed_round.status_code, 409, changed_round.text)
        revised = self.proposal(round_number=2, round_name="Technical", reschedule_interview_id=source["id"],
            scheduled_time=(self.at + timedelta(hours=2)).isoformat())
        self.assertEqual(self.review(revised).status_code, 200)
        own = self.client.get(f"/students/{self.sid}/interviews", headers=self.a["student"]["headers"]).json()["items"]
        booked = next(i for i in own if i["schedule_id"] == revised["id"])
        self.assertEqual((booked["round_number"], booked["round_name"]), (2, "Technical"))
        self.assertEqual(next(i for i in own if i["id"] == source["id"])["status"], "cancelled")

    def test_new_tables_force_rls_without_application_filters(self):
        row = self.admin_constraint()
        for model in (CalendarSettings, CalendarConstraint):
            with self.subTest(table=model.__tablename__), tenant_session(self.a["college"]) as session:
                # Deliberately omit application filters only to test the second isolation layer.
                visible = session.scalars(select(model)).all()
                self.assertTrue(visible)
                self.assertTrue(all(r.college_id == self.a["college"] for r in visible))
            with SessionLocal() as session:
                self.assertEqual(session.scalars(select(model)).all(), [])
        with tenant_session(self.b["college"]) as session:
            self.assertIsNone(session.scalar(select(CalendarConstraint).where(CalendarConstraint.id == row["id"])))
        for model in (CalendarSettings, CalendarConstraint):
            with self.subTest(write=model.__tablename__), self.assertRaises(DBAPIError) as blocked:
                with tenant_session(self.a["college"]) as session:
                    current = session.scalar(select(model).where(model.college_id == self.a["college"]))
                    session.execute(update(model).where(model.college_id == self.a["college"], model.id == current.id).values(college_id=self.b["college"]))
            self.assertIn("row-level security", str(blocked.exception).lower())
        with self.assertRaises(DBAPIError) as blocked:
            with tenant_session(self.b["college"]) as session:
                session.add(CalendarConstraint(college_id=self.a["college"], kind="unavailable", scope="student", student_id=self.sid,
                    starts_at=self.at, ends_at=self.at + timedelta(minutes=30), label="Local RLS insert denial",
                    created_by=self.a["admin"]["user"]["user_id"]))
                session.flush()
        self.assertIn("row-level security", str(blocked.exception).lower())
        with self.assertRaises(DBAPIError) as blocked:
            with tenant_session(self.b["college"]) as session:
                session.add(CalendarSettings(college_id=self.a["college"]))
                session.flush()
        self.assertIn("row-level security", str(blocked.exception).lower())
        with engine.connect() as connection:
            policies = connection.execute(text("SELECT tablename,policyname,qual,with_check FROM pg_policies "
                "WHERE schemaname=current_schema() AND tablename IN ('calendar_settings','calendar_constraints')")).all()
            self.assertEqual(len(policies), 2)
            self.assertTrue(all(p.policyname == "college_isolation" and "college_id" in p.qual and "college_id" in p.with_check for p in policies))
            tables = connection.execute(text("SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class "
                "WHERE relname IN ('calendar_settings','calendar_constraints')")).all()
            self.assertEqual(len(tables), 2)
            self.assertTrue(all(t.relrowsecurity and t.relforcerowsecurity for t in tables))


if __name__ == "__main__":
    unittest.main()
