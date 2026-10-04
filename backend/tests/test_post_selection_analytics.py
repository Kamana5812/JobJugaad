"""Recorded post-selection analytics checks on isolated local PostgreSQL only.

Fixtures deliberately retain history and use unique drives, so repeated runs do
not need to delete or overwrite existing test records. They are not outcomes
from real students, employers, or colleges.
"""
import json
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select, update

from auth import hash_password, issue_token
from database import engine, initialize_schema, tenant_session
from engines.offers import snapshot
from main import app
from models import (AccountAccess, Application, Company, Interview, Job, Match,
    Offer, OfferEvent, ScheduleEvent, Student, User)
from schemas import JobInput


class PostSelectionAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine is None
                or engine.url.host not in ("127.0.0.1", "localhost")
                or engine.url.database not in ("jobjugaad_test", "jobjugaad_test_utf8")):
            raise RuntimeError("Explicit isolated localhost analytics test database required.")
        initialize_schema()
        cls.client = TestClient(app)
        cls.suffix = uuid.uuid4().hex[:12]
        cls.password_hash = hash_password("Local-funnel-fixture-2026")
        cls.accounts = []
        for college in (10226, 10229, 1):
            account = dict(college=college)
            for role in ("admin", "recruiter", "student"):
                account[role] = cls.new_user(account, role)
            with tenant_session(college) as session:
                company = Company(college_id=college,
                    recruiter_user_id=account["recruiter"]["user_id"],
                    name=f"Controlled funnel company {cls.suffix}", industry="Testing")
                session.add(company); session.flush()
                account["company_id"] = company.id
            cls.accounts.append(account)
        cls.allowlist = patch.dict(os.environ, {"ADMIN_ACCOUNTS": json.dumps([
            dict(email=a["admin"]["email"], college_id=a["college"])
            for a in cls.accounts])})
        cls.allowlist.start()

    @classmethod
    def tearDownClass(cls):
        cls.allowlist.stop()

    @classmethod
    def new_user(cls, account, role="student"):
        college = account["college"]
        with tenant_session(college) as session:
            user = User(college_id=college, role=role,
                email=f"funnel-{role}-{uuid.uuid4().hex}@test.invalid",
                password_hash=cls.password_hash)
            session.add(user); session.flush()
            session.add(AccountAccess(college_id=college, user_id=user.id,
                email_verified_at=datetime.now(timezone.utc), approval_status="approved"))
            student = None
            if role == "student":
                student = Student(college_id=college, user_id=user.id,
                    name=f"Controlled funnel student {uuid.uuid4().hex[:8]}", branch="CSE", cgpa=8)
                session.add(student); session.flush()
            token = issue_token(user, student=student, session=session).access_token
            return dict(user_id=user.id, student_id=student.id if student else None,
                email=user.email, headers={"Authorization": "Bearer " + token})

    def setUp(self):
        self.a, self.b, self.archive = self.accounts
        self.job = self.new_job(self.a)
        self.other_job = self.new_job(self.b)

    def new_job(self, account):
        data = JobInput(title=f"Controlled funnel drive {uuid.uuid4().hex[:10]}", ctc=6,
            min_cgpa=5, eligible_branches=["CSE"],
            required_skills=[dict(skill_name="python", min_proficiency=60)]).model_dump()
        with tenant_session(account["college"]) as session:
            job = Job(college_id=account["college"], company_id=account["company_id"], **data)
            session.add(job); session.flush()
            return job.id

    def interview(self, account=None, student=None, job=None, status="selected", synthetic=False, round_number=1):
        account = account or self.a
        student = student or account["student"]
        with tenant_session(account["college"]) as session:
            start = datetime.now(timezone.utc) - timedelta(days=2)
            row = Interview(college_id=account["college"], student_id=student["student_id"],
                job_id=job or self.job, scheduled_time=start, end_time=start + timedelta(minutes=30),
                venue="Controlled funnel room", panel_id="Controlled funnel panel",
                status=status, round_number=round_number, round_name=f"Round {round_number}",
                seed_key=f"phase4:funnel:{uuid.uuid4().hex}" if synthetic else None)
            session.add(row); session.flush()
            return row.id

    def new_offer(self, account=None, student=None, job=None):
        account = account or self.a
        identity = self.interview(account, student, job)
        response = self.client.post("/admin/offers", headers=account["admin"]["headers"],
            json=dict(interview_id=identity, reason="Controlled local selected interview offer"))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def admin_change(self, row, stage, value, account=None, reason="Controlled local officer records stage", expected=200):
        account = account or self.a
        response = self.client.put(f"/admin/offers/{row['id']}", headers=account["admin"]["headers"],
            json=dict(stage=stage, value=value, version=row["version"], reason=reason))
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def student_change(self, row, action, student=None, reason="Controlled local student records response", expected=200):
        student = student or self.a["student"]
        response = self.client.post(f"/students/{student['student_id']}/offers/{row['id']}/actions",
            headers=student["headers"], json=dict(action=action, version=row["version"], reason=reason))
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def import_offer(self, student=None, **stages):
        """Import final synthetic state, matching the seed's one-snapshot history."""
        student = student or self.a["student"]
        identity = self.interview(student=student, synthetic=True)
        with tenant_session(self.a["college"]) as session:
            row = Offer(college_id=self.a["college"], student_id=student["student_id"],
                job_id=self.job, interview_id=identity, ctc=6, is_synthetic=True,
                seed_key=f"phase4:funnel-offer:{uuid.uuid4().hex}", **stages)
            session.add(row); session.flush()
            session.add(OfferEvent(college_id=self.a["college"], offer_id=row.id,
                actor_user_id=None, action="synthetic_import",
                reason="Synthetic outcome sampled from proposed assumptions; not a human decision.",
                snapshot={"before": None, "after": snapshot(row)}))
            return row.id

    def report(self, account=None, job=None, expected=200, **filters):
        account = account or self.a
        params = dict(job_id=self.job if job is None else job, **filters)
        response = self.client.get("/admin/analytics/post-selection",
            headers=account["admin"]["headers"], params=params)
        self.assertEqual(response.status_code, expected, response.text)
        return response.json()

    def stages(self, report):
        return {row["key"]: row for row in report["stages"]}

    def milestones(self, report):
        return {row["key"]: row for row in report["milestones"]}

    def closures(self, report):
        return {row["key"]: row for row in report["closures"]}

    def counts(self, report):
        return [row["count"] for row in report["stages"]]

    def verified_offer(self, student=None, accept_first=True):
        row = self.new_offer(student=student)
        row = self.admin_change(row, "offer_letter_status", "issued")
        if accept_first:
            row = self.student_change(row, "accept", student)
        row = self.student_change(row, "submit_documents", student)
        row = self.admin_change(row, "verification_status", "verified")
        if not accept_first:
            row = self.student_change(row, "accept", student)
        return row

    def direct_offer(self, student=None, **stages):
        """Legacy state without events tests missing evidence, not invented reasons."""
        student = student or self.a["student"]
        identity = self.interview(student=student)
        with tenant_session(self.a["college"]) as session:
            row = Offer(college_id=self.a["college"], student_id=student["student_id"],
                job_id=self.job, interview_id=identity, ctc=6, **stages)
            session.add(row); session.flush()
            return row.id

    def test_empty_drive_has_no_fabricated_percentages_or_dropout_reasons(self):
        result = self.report()
        self.assertEqual(result["scope"], "recorded")
        self.assertEqual(result["college_id"], self.a["college"])
        self.assertEqual(result["job_id"], self.job)
        self.assertEqual(result["cohort"]["selected_pairs"], 0)
        self.assertEqual(self.counts(result), [0, 0, 0, 0, 0])
        self.assertTrue(all(row["conversion_percent"] is None for row in result["stages"]))
        self.assertEqual(result["reason_total"], 0)
        self.assertEqual(result["reasons"], [])
        self.assertTrue(result["methodology"] and result["limitations"] and result["scope_explanation"])
        self.assertTrue(all(row["explanation"] for row in result["stages"] + result["milestones"] + result["closures"]))

    def test_acceptance_then_verification_and_explicit_joining(self):
        row = self.new_offer()
        self.assertEqual(self.counts(self.report()), [1, 0, 0, 0, 0])
        row = self.admin_change(row, "offer_letter_status", "issued")
        row = self.student_change(row, "accept")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 1, 1, 0, 0])
        self.assertEqual(self.milestones(result)["verified"]["count"], 0)
        row = self.student_change(row, "submit_documents")
        row = self.admin_change(row, "verification_status", "verified")
        self.assertEqual(self.counts(self.report()), [1, 1, 1, 1, 0])
        self.admin_change(row, "joining_status", "joined")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 1, 1, 1, 1])
        self.assertEqual(result["cohort"]["distinct_students"], 1)
        self.assertEqual(sum(row["count"] for row in result["closures"]), 0)

    def test_verification_before_acceptance_is_an_independent_milestone(self):
        row = self.new_offer()
        row = self.admin_change(row, "offer_letter_status", "issued")
        row = self.student_change(row, "submit_documents")
        row = self.admin_change(row, "verification_status", "verified")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 1, 0, 0, 0])
        self.assertEqual(self.milestones(result)["verified"]["count"], 1)
        self.assertEqual(self.milestones(result)["verified_without_acceptance"]["count"], 1)
        row = self.student_change(row, "accept")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 1, 1, 1, 0])
        self.assertEqual(self.milestones(result)["verified_without_acceptance"]["count"], 0)
        self.admin_change(row, "joining_status", "not_joined", reason="Student reported a change of joining plans")
        result = self.report()
        self.assertEqual(self.closures(result)["not_joined"]["count"], 1)
        self.assertEqual(self.counts(result), [1, 1, 1, 1, 0])

    def test_correction_and_withdrawal_preserve_historical_milestones(self):
        row = self.verified_offer()
        row = self.admin_change(row, "documents_status", "changes_requested")
        self.assertEqual(row["verification_status"], "pending")
        self.assertEqual(self.counts(self.report()), [1, 1, 1, 1, 0])
        self.admin_change(row, "offer_letter_status", "withdrawn", reason="Employer withdrew this recorded offer")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 1, 1, 1, 0])
        self.assertEqual(self.closures(result)["withdrawn"]["count"], 1)
        self.assertEqual(result["reasons"], [dict(closure="withdrawn",
            reason="Employer withdrew this recorded offer", reason_source="recorded_action",
            count=1, synthetic_count=0, recorded_count=1)])

    def test_unissued_withdrawal_is_closed_without_inventing_issuance(self):
        row = self.new_offer()
        self.admin_change(row, "offer_letter_status", "withdrawn", reason="Role cancelled before letter issuance")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertEqual(result["data_quality"]["withdrawn_without_issuance_evidence"], 1)
        self.assertEqual(self.stages(result)["issued"]["not_reached_from_previous"], 1)
        self.assertEqual(self.stages(result)["issued"]["closed_from_previous"], 1)
        self.assertEqual(self.stages(result)["issued"]["pending_from_previous"], 0)

    def test_pending_stage_gaps_are_not_labelled_as_dropouts(self):
        self.new_offer()
        result = self.report()
        self.assertEqual(self.stages(result)["issued"]["pending_from_previous"], 1)
        self.assertEqual(self.stages(result)["issued"]["closed_from_previous"], 0)
        self.assertEqual(sum(row["count"] for row in result["closures"]), 0)
        self.assertEqual(result["reasons"], [])

    def test_selected_rounds_deduplicate_and_shortlists_are_not_selection(self):
        self.interview(round_number=1)
        self.interview(round_number=2)
        unrelated = self.new_user(self.a)
        self.interview(student=unrelated, status="scheduled")
        with tenant_session(self.a["college"]) as session:
            session.add(Application(college_id=self.a["college"], job_id=self.job,
                student_id=unrelated["student_id"], status="shortlisted", cover_note="Controlled shortlist",
                evidence_snapshot={}))
            session.add(Match(college_id=self.a["college"], job_id=self.job,
                student_id=unrelated["student_id"], match_score=99, eligible=True,
                factor_breakdown=[], missing_requirements=[], skill_gaps=[],
                explanation="Controlled eligible match is not a selected interview.",
                next_step="Human interview decision remains separate.", methodology="Test fixture", override_action="promote"))
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertEqual(result["cohort"]["offers"], 0)
        self.assertEqual(result["cohort"]["without_offer"], 1)
        self.assertEqual(result["cohort"]["distinct_students"], 1)

    def test_selected_outcome_revised_to_rejected_retains_valid_audit_evidence(self):
        identity = self.interview()
        response = self.client.put(f"/admin/interviews/{identity}/status", headers=self.a["admin"]["headers"],
            json=dict(status="rejected", reason="Controlled officer revises interview outcome after review"))
        self.assertEqual(response.status_code, 200, response.text)
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertGreaterEqual(result["data_quality"]["selection_from_history"], 1)

    def test_consistently_linked_offer_retains_selection_when_outcome_is_revised_without_history(self):
        row = self.new_offer()
        with tenant_session(self.a["college"]) as session:
            session.execute(update(Interview).where(Interview.college_id == self.a["college"],
                Interview.id == row["interview_id"]).values(status="rejected"))
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertEqual(result["cohort"]["offers"], 1)
        self.assertEqual(result["data_quality"]["selection_from_linked_offer"], 1)

    def test_mismatched_offer_interview_is_warned_and_excluded_from_offer_milestones(self):
        other = self.new_user(self.a)
        identity = self.interview(student=other)
        with tenant_session(self.a["college"]) as session:
            # Existing individual tenant foreign keys cannot prove that the
            # linked interview belongs to the same student-drive pair.
            session.add(Offer(college_id=self.a["college"], student_id=self.a["student"]["student_id"],
                job_id=self.job, interview_id=identity, ctc=6, offer_letter_status="issued"))
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertEqual(result["cohort"]["offers"], 0)
        self.assertEqual(result["cohort"]["without_offer"], 1)
        self.assertEqual(result["data_quality"]["offers_with_mismatched_interview"], 1)

    def test_file_audit_snapshots_do_not_duplicate_cases_or_change_offer_milestones(self):
        row = self.verified_offer()
        before = self.report()
        with tenant_session(self.a["college"]) as session:
            current = session.scalar(select(Offer).where(Offer.college_id == self.a["college"], Offer.id == row["id"]))
            for action in ("document_uploaded", "document_reviewed"):
                session.add(OfferEvent(college_id=self.a["college"], offer_id=current.id,
                    actor_user_id=self.a["admin"]["user_id"], action=action,
                    reason="Controlled file audit does not record an offer-stage transition",
                    snapshot={"before": snapshot(current), "after": snapshot(current)}))
        after = self.report()
        for key in ("cohort", "stages", "milestones", "closures", "reasons", "data_quality"):
            self.assertEqual(after[key], before[key])

    def test_multiple_drives_count_pairs_separately_and_students_once(self):
        baseline = self.client.get("/admin/analytics/post-selection", headers=self.a["admin"]["headers"],
            params=dict(scope="recorded")).json()
        student = self.new_user(self.a)
        second_job = self.new_job(self.a)
        self.new_offer(student=student)
        self.new_offer(student=student, job=second_job)
        result = self.client.get("/admin/analytics/post-selection", headers=self.a["admin"]["headers"],
            params=dict(scope="recorded")).json()
        self.assertEqual(result["cohort"]["selected_pairs"], baseline["cohort"]["selected_pairs"] + 2)
        self.assertEqual(result["cohort"]["distinct_students"], baseline["cohort"]["distinct_students"] + 1)
        self.assertEqual(result["cohort"]["offers"], baseline["cohort"]["offers"] + 2)
        self.assertEqual(self.report()["cohort"]["selected_pairs"], 1)

    def test_repeated_reads_and_rejected_retries_do_not_duplicate_milestones(self):
        row = self.new_offer()
        issued = self.admin_change(row, "offer_letter_status", "issued")
        before = self.report()
        self.admin_change(row, "offer_letter_status", "issued", expected=409)
        duplicate = self.client.post("/admin/offers", headers=self.a["admin"]["headers"],
            json=dict(interview_id=row["interview_id"], reason="Controlled duplicate offer retry"))
        self.assertEqual(duplicate.status_code, 409, duplicate.text)
        after = self.report()
        for key in ("cohort", "stages", "milestones", "closures", "reasons", "data_quality"):
            self.assertEqual(after[key], before[key])
        with tenant_session(self.a["college"]) as session:
            events = session.scalars(select(OfferEvent).where(OfferEvent.college_id == self.a["college"],
                OfferEvent.offer_id == issued["id"])).all()
            self.assertEqual(len(events), 2)

    def test_synthetic_import_has_explicit_provenance_without_claiming_a_human_cause(self):
        self.import_offer(offer_letter_status="issued", documents_status="submitted", verification_status="verified",
            acceptance_status="accepted", joining_status="not_joined")
        recorded = self.report()
        self.assertEqual(recorded["cohort"]["selected_pairs"], 0)
        self.assertEqual(recorded["cohort"]["excluded_pairs"], 1)
        result = self.report(scope="synthetic")
        self.assertEqual(self.counts(result), [1, 1, 1, 1, 0])
        self.assertEqual(result["cohort"]["synthetic_pairs"], 1)
        self.assertEqual(result["cohort"]["recorded_pairs"], 0)
        self.assertEqual(result["reasons"][0]["reason_source"], "synthetic_import")
        self.assertEqual(result["reasons"][0]["synthetic_count"], 1)
        self.assertEqual(result["reasons"][0]["recorded_count"], 0)
        self.assertNotEqual(result["reasons"][0]["reason_source"], "recorded_action")

    def test_seeded_interview_provenance_and_names_do_not_relabel_recorded_cases(self):
        self.interview()
        self.interview(student=self.new_user(self.a), synthetic=True)
        with tenant_session(self.a["college"]) as session:
            session.execute(update(Job).where(Job.college_id == self.a["college"], Job.id == self.job)
                .values(title="Synthetic demo words in a user-entered title"))
        recorded, synthetic, combined = self.report(), self.report(scope="synthetic"), self.report(scope="all")
        self.assertEqual(recorded["cohort"]["selected_pairs"], 1)
        self.assertEqual(synthetic["cohort"]["selected_pairs"], 1)
        self.assertEqual(combined["cohort"]["selected_pairs"], 2)
        self.assertEqual(combined["cohort"]["recorded_pairs"], 1)
        self.assertEqual(combined["cohort"]["synthetic_pairs"], 1)

    def test_archived_college_records_are_excluded_by_default_even_without_flags(self):
        job = self.new_job(self.archive)
        self.interview(account=self.archive, student=self.archive["student"], job=job)
        recorded = self.report(account=self.archive, job=job)
        self.assertTrue(recorded["archive_demo"])
        self.assertEqual(recorded["cohort"]["selected_pairs"], 0)
        self.assertEqual(recorded["cohort"]["excluded_pairs"], 1)
        result = self.report(account=self.archive, job=job, scope="synthetic")
        self.assertEqual(result["cohort"]["selected_pairs"], 1)
        self.assertEqual(result["cohort"]["synthetic_pairs"], 1)

    def test_invalid_offer_identity_snapshots_do_not_supply_issuance_or_reasons(self):
        row = self.new_offer()
        with tenant_session(self.a["college"]) as session:
            current = session.scalar(select(Offer).where(Offer.college_id == self.a["college"], Offer.id == row["id"]))
            forged = {**snapshot(current), "offer_letter_status": "issued", "student_id": self.new_user(self.a)["student_id"]}
            session.add(OfferEvent(college_id=self.a["college"], offer_id=row["id"], actor_user_id=self.a["admin"]["user_id"],
                action="offer_letter_status:issued", reason="This mismatched snapshot must not establish issuance",
                snapshot={"before": None, "after": forged}))
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertEqual(result["data_quality"]["invalid_offer_history_events"], 1)
        self.assertEqual(result["reasons"], [])

    def test_invalid_selection_snapshot_does_not_select_an_unselected_pair(self):
        identity = self.interview(status="rejected")
        with tenant_session(self.a["college"]) as session:
            session.add(ScheduleEvent(college_id=self.a["college"], interview_id=identity,
                actor_user_id=self.a["admin"]["user_id"], action="interview_status",
                reason="Controlled mismatched identity must not establish selection",
                snapshot={"before": None, "after": dict(id=identity, student_id=self.a["student"]["student_id"],
                    job_id=self.other_job, status="selected")}))
        result = self.report()
        self.assertEqual(self.counts(result), [0, 0, 0, 0, 0])
        self.assertEqual(result["data_quality"]["invalid_selection_history_events"], 1)

    def test_legacy_missing_history_reports_unknown_reason_without_invented_prior_stages(self):
        self.direct_offer(offer_letter_status="withdrawn")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertEqual(result["data_quality"]["offers_without_history"], 1)
        self.assertEqual(result["data_quality"]["withdrawn_without_issuance_evidence"], 1)
        self.assertEqual(self.closures(result)["withdrawn"]["missing_reason_count"], 1)
        self.assertEqual(result["reasons"][0]["reason_source"], "missing")

    def test_legacy_accepted_without_issuance_is_warned_and_not_inferred(self):
        self.direct_offer(offer_letter_status="draft", acceptance_status="accepted")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 0, 0, 0, 0])
        self.assertEqual(self.milestones(result)["accepted"]["count"], 1)
        self.assertEqual(result["data_quality"]["accepted_without_issuance_evidence"], 1)

    def test_legacy_closure_priority_counts_each_pair_once(self):
        identity = self.direct_offer(offer_letter_status="withdrawn", acceptance_status="declined", joining_status="not_joined")
        with tenant_session(self.a["college"]) as session:
            row = session.scalar(select(Offer).where(Offer.college_id == self.a["college"], Offer.id == identity))
            session.add(OfferEvent(college_id=self.a["college"], offer_id=identity,
                actor_user_id=self.a["admin"]["user_id"], action="offer_letter_status:withdrawn",
                reason="Recorded withdrawal takes precedence in this contradictory legacy case",
                snapshot={"before": None, "after": snapshot(row)}))
        result = self.report()
        self.assertEqual(self.closures(result)["withdrawn"]["count"], 1)
        self.assertEqual(self.closures(result)["declined"]["count"], 0)
        self.assertEqual(self.closures(result)["not_joined"]["count"], 0)
        self.assertEqual(sum(row["count"] for row in result["reasons"]), 1)

    def test_document_rejection_is_not_a_terminal_offer_closure(self):
        row = self.new_offer()
        row = self.admin_change(row, "offer_letter_status", "issued")
        row = self.student_change(row, "accept")
        row = self.student_change(row, "submit_documents")
        self.admin_change(row, "verification_status", "rejected", reason="Supporting evidence requires further human review")
        result = self.report()
        self.assertEqual(self.counts(result), [1, 1, 1, 0, 0])
        self.assertEqual(self.stages(result)["verified"]["pending_from_previous"], 1)
        self.assertEqual(self.stages(result)["verified"]["closed_from_previous"], 0)
        self.assertEqual(sum(row["count"] for row in result["closures"]), 0)
        self.assertEqual(result["reasons"], [])

    def test_terminal_reasons_group_and_paginate_without_changing_totals(self):
        for reason in ("Student preferred another recorded offer", "Student preferred another recorded offer", "Student paused joining plans"):
            student = self.new_user(self.a)
            row = self.new_offer(student=student)
            row = self.admin_change(row, "offer_letter_status", "issued")
            self.student_change(row, "decline", student, reason=reason)
        first, second, entire = self.report(limit=1), self.report(limit=1, offset=1), self.report(limit=50)
        self.assertEqual(first["reason_total"], 2)
        self.assertEqual(second["reason_total"], 2)
        self.assertEqual(len(first["reasons"]), 1)
        self.assertEqual(first["reasons"] + second["reasons"], entire["reasons"])
        self.assertEqual(sum(row["count"] for row in entire["reasons"]), 3)
        self.assertEqual(self.closures(entire)["declined"]["count"], 3)
        self.assertEqual(self.closures(entire)["declined"]["distinct_students"], 3)
        self.assertEqual(first["cohort"], second["cohort"])
        self.assertTrue(all(row["reason_source"] == "recorded_action" for row in entire["reasons"]))

    def test_role_allowlist_verified_admin_and_current_database_role_are_enforced(self):
        route = "/admin/analytics/post-selection"
        self.assertEqual(self.client.get(route).status_code, 401)
        for role in ("student", "recruiter"):
            self.assertEqual(self.client.get(route, headers=self.a[role]["headers"]).status_code, 403)
        with patch.dict(os.environ, {"ADMIN_ACCOUNTS": "[]"}):
            self.assertEqual(self.client.get(route, headers=self.a["admin"]["headers"]).status_code, 403)
        for column, value, expected in (("role", "recruiter", 401), ("email_verified_at", None, 403)):
            model = User if column == "role" else AccountAccess
            identity = User.id if column == "role" else AccountAccess.user_id
            restore = "admin" if column == "role" else datetime.now(timezone.utc)
            with tenant_session(self.a["college"]) as session:
                session.execute(update(model).where(model.college_id == self.a["college"],
                    identity == self.a["admin"]["user_id"]).values(**{column: value}))
            try:
                self.assertEqual(self.client.get(route, headers=self.a["admin"]["headers"]).status_code, expected)
            finally:
                with tenant_session(self.a["college"]) as session:
                    session.execute(update(model).where(model.college_id == self.a["college"],
                        identity == self.a["admin"]["user_id"]).values(**{column: restore}))

    def test_tenant_scopes_never_expose_another_colleges_reasons_or_drives(self):
        foreign = self.new_offer(account=self.b, student=self.b["student"], job=self.other_job)
        self.admin_change(foreign, "offer_letter_status", "withdrawn", account=self.b,
            reason="FOREIGN-COLLEGE-PRIVATE-CLOSURE-SENTINEL")
        self.interview()
        own = self.report(scope="all")
        self.assertEqual(own["cohort"]["selected_pairs"], 1)
        self.assertEqual(own["reasons"], [])
        self.assertNotIn("FOREIGN-COLLEGE-PRIVATE", json.dumps(own))
        self.report(job=self.other_job, expected=404)
        foreign_report = self.report(account=self.b, job=self.other_job, scope="all")
        self.assertEqual(foreign_report["reasons"][0]["reason"], "FOREIGN-COLLEGE-PRIVATE-CLOSURE-SENTINEL")
        self.assertIn(self.job, {row["id"] for row in own["drives"]})
        self.assertNotIn(self.other_job, {row["id"] for row in own["drives"]})

    def test_filter_validation_and_openapi_contract(self):
        route = "/admin/analytics/post-selection"
        for values in (dict(scope="real"), dict(job_id=0), dict(offset=-1), dict(limit=0), dict(limit=51)):
            self.assertEqual(self.client.get(route, headers=self.a["admin"]["headers"], params=values).status_code, 422)
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn(route, paths)
        self.assertIn("get", paths[route])

    def export_browser_fixture(self):
        """Called explicitly only after passing tests; exports local dummy data."""
        first = self.new_user(self.a)
        joined = self.verified_offer(student=first)
        self.admin_change(joined, "joining_status", "joined")
        second = self.new_user(self.a)
        declined = self.admin_change(self.new_offer(student=second), "offer_letter_status", "issued")
        self.student_change(declined, "decline", second, reason="Controlled preview: student preferred another offer")
        self.interview(student=self.new_user(self.a))
        self.import_offer(student=self.new_user(self.a), offer_letter_status="issued", documents_status="submitted",
            verification_status="verified", acceptance_status="accepted", joining_status="not_joined")
        recorded, combined = self.report(), self.report(scope="all")
        self.assertEqual(self.counts(recorded), [3, 2, 1, 1, 1])
        self.assertEqual(self.counts(combined), [4, 3, 2, 2, 1])
        path = Path(__file__).resolve().parents[2] / ".local" / "post-selection-browser-fixture.json"
        path.write_text(json.dumps(dict(database_name=engine.url.database, college_id=self.a["college"],
            college_code=226, admin_email=self.a["admin"]["email"], password="Local-funnel-fixture-2026",
            job_id=self.job, recorded_stage_counts=self.counts(recorded), all_stage_counts=self.counts(combined),
            recorded_reasons=recorded["reasons"], all_reasons=combined["reasons"],
            note="Controlled local PostgreSQL fixtures only; no real or production credentials or outcomes."), indent=2), encoding="utf-8")
        (path.parent / "post-selection-render-data.json").write_text(json.dumps(dict(recorded=recorded,
            synthetic=self.report(scope="synthetic"), all=combined), indent=2), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()
