"""Meaningful rule and PostgreSQL integration tests; localhost only."""
import os
import unittest
import uuid
from types import SimpleNamespace as Obj
from fastapi.testclient import TestClient
from sqlalchemy import select, text, update, func
from sqlalchemy.exc import DBAPIError
from database import engine, tenant_session, SessionLocal
from main import app
from models import Company, Job, Match, MatchOverride, User
from schemas import JobInput, MatchingWeights
from engines.matching import calculate_match
from engines.skill_gap import skill_gaps
from seed import seed_students, seed_companies, DEMO_DRIVES


class MatchingRuleTests(unittest.TestCase):
    def setUp(self):
        self.student = Obj(cgpa=8, branch="CSE", backlog_count=0, aptitude_score=60, communication_score=90, interview_score=None)
        self.job = Obj(**JobInput(title="Test", ctc=6, min_cgpa=6, eligible_branches=["CSE"],
            required_skills=[dict(skill_name="python", min_proficiency=80), dict(skill_name="sql", min_proficiency=60)]).model_dump())
        self.skills = [Obj(skill_name="Python", proficiency=40), Obj(skill_name="sql", proficiency=90)]
        self.projects = [Obj(title="Python service", description="SQL data")]
        self.certs = [Obj(title="Course")]

    def score(self):
        return calculate_match(self.student, self.skills, self.projects, self.certs, self.job)

    def test_normalized_rule_and_no_confidence(self):
        result = self.score()
        self.assertEqual([f.value for f in result.factor_breakdown], [75, 100, 80, 50, 25])
        self.assertEqual([f.contribution for f in result.factor_breakdown], [30, 20, 16, 7.5, 1.25])
        self.assertEqual(result.match_score, 74.75)
        self.assertTrue(result.eligible)
        self.assertNotIn("confidence", result.model_dump())
        self.assertIn("unvalidated", result.methodology)
        self.assertEqual([g.status for g in result.skill_gaps], ["gap", "on-track"])

    def test_threshold_boundary_and_fixed_explanation(self):
        self.job.min_match_score = 74.75
        self.assertTrue(self.score().eligible)
        self.job.min_match_score = 74.76
        result = self.score()
        self.assertFalse(result.eligible)
        self.assertEqual(result.explanation, "Below Threshold: The student's CGPA meets the eligibility criteria, but the required skill set shows a gap in python and the weighted match score 74.75/100 is below the required 74.76/100 threshold.")
        self.assertTrue(result.missing_requirements and result.next_step)

    def test_hard_rule_cannot_be_overruled_by_score(self):
        self.student.branch = "ME"
        result = self.score()
        self.assertFalse(result.eligible)
        self.assertGreater(result.match_score, 60)
        self.assertIn("branch ME", result.explanation)
        self.skills[0].proficiency = 100
        result = self.score()
        self.assertIn("no required skill gap was found", result.explanation)
        self.assertNotIn("shows a gap in python", result.explanation)

    def test_keywords_missing_evidence_and_status_boundaries(self):
        self.job.required_skills = [dict(skill_name="java", min_proficiency=60)]
        self.projects = [Obj(title="JavaScript app", description="React")]
        self.assertEqual(self.score().factor_breakdown[1].value, 0)
        gaps = skill_gaps([Obj(skill_name="java", proficiency=29)], self.job.required_skills)
        self.assertEqual(gaps[0]["status"], "critical")
        gaps = skill_gaps([Obj(skill_name="java", proficiency=30)], self.job.required_skills)
        self.assertEqual(gaps[0]["status"], "gap")
        self.student.cgpa = None
        self.student.aptitude_score = self.student.communication_score = None
        self.skills, self.projects, self.certs = [], [], []
        result = self.score()
        self.assertEqual(result.match_score, 0)
        self.assertTrue(all(f.missing for f in result.factor_breakdown))
        with self.assertRaises(ValueError):
            MatchingWeights(skills=90)


class TalentIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("127.0.0.1", "localhost"):
            raise RuntimeError("Explicit localhost test database required.")
        cls.client = TestClient(app)
        cls.client.__enter__()
        cls.recruiters = []
        for college in (1, 1, 2):
            payload = dict(email=f"{uuid.uuid4().hex}@talent.test", password="Synthetic-only-2026", college_id=college,
                company=dict(name="Synthetic Test Company", industry="Software"))
            response = cls.client.post("/auth/recruiter/signup", json=payload)
            assert response.status_code == 201, response.text
            result = response.json()
            headers = {"Authorization": "Bearer " + result["access_token"]}
            job = cls.client.post("/recruiters/jobs", headers=headers, json=DEMO_DRIVES[0].model_dump())
            assert job.status_code == 201, job.text
            cls.recruiters.append((payload, result, headers, job.json()))
        # Ensure each tenant has at least one complete candidate, no real student data.
        for college in (1, 2):
            response = cls.client.post("/auth/signup", json=dict(name="Synthetic Perfect Candidate", college_id=college,
                email=f"{uuid.uuid4().hex}@talent.test", password="Synthetic-only-2026")).json()
            headers = {"Authorization": "Bearer " + response["access_token"]}
            cls.student_headers = headers
            cls.client.put(f"/students/{response['user']['student_id']}", headers=headers, json=dict(
                name="Synthetic Perfect Candidate", branch="CSE", cgpa=9, backlog_count=0,
                aptitude_score=80, communication_score=90, interview_score=80,
                skills=[dict(skill_name="python", proficiency=90), dict(skill_name="sql", proficiency=90)],
                projects=[dict(title="Python SQL app", description="Synthetic practical example")], certifications=[]))
        for _, _, headers, job in cls.recruiters:
            response = cls.client.post(f"/recruiters/jobs/{job['id']}/matching", headers=headers)
            assert response.status_code == 200, response.text
            candidate = cls.client.get(f"/recruiters/jobs/{job['id']}/matches?status=all", headers=headers).json()["candidates"][0]
            cls.client.post(f"/recruiters/jobs/{job['id']}/matches/{candidate['id']}/override", headers=headers,
                json=dict(action="promote", reason="Synthetic human review for integration test."))

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_auth_company_and_owned_drives(self):
        payload, account, headers, job = self.recruiters[0]
        self.assertEqual(account["user"]["role"], "recruiter")
        login = self.client.post("/auth/login", json={k:v for k,v in payload.items() if k != "company"})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get("/auth/me", headers=headers).json()["company_id"], job["company_id"])
        self.assertEqual(self.client.put("/recruiters/company", headers=headers, json=dict(name="Updated Synthetic Company", industry="Testing")).status_code, 200)
        self.assertEqual(self.client.get("/recruiters/company", headers=headers).json()["name"], "Updated Synthetic Company")
        self.assertEqual(self.client.get("/recruiters/jobs").status_code, 401)
        self.assertEqual(self.client.get("/recruiters/jobs", headers=self.student_headers).status_code, 403)
        for _, _, other_headers, other_job in self.recruiters[1:]:
            self.assertEqual(self.client.get(f"/recruiters/jobs/{job['id']}/matches", headers=other_headers).status_code, 404)
            self.assertEqual(self.client.post(f"/recruiters/jobs/{job['id']}/matching", headers=other_headers).status_code, 404)
            self.assertEqual(self.client.post(f"/recruiters/jobs/{job['id']}/matches/1/override", headers=other_headers,
                json=dict(action="reject", reason="Attempt with wrong owner")).status_code, 404)
        invalid = {**DEMO_DRIVES[0].model_dump(), "college_id": 2}
        self.assertEqual(self.client.post("/recruiters/jobs", headers=headers, json=invalid).status_code, 422)

    def test_sort_override_audit_and_rerun(self):
        _, _, headers, job = self.recruiters[0]
        path = f"/recruiters/jobs/{job['id']}"
        all_rows = self.client.get(path + "/matches?status=all&limit=100", headers=headers).json()
        scores = [m["match_score"] for m in all_rows["candidates"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        candidate = all_rows["candidates"][0]
        before = candidate["match_score"]
        result = self.client.post(path + f"/matches/{candidate['id']}/override", headers=headers,
            json=dict(action="reject", reason="Synthetic rejection after human review")).json()
        self.assertEqual(result["shortlist_status"], "excluded")
        self.assertEqual(result["match_score"], before)
        self.assertEqual(result["audit"][-1]["evidence_at_action"]["factor_breakdown"], result["factor_breakdown"])
        self.client.post(path + "/matching", headers=headers)
        result = self.client.get(path + "/matches?status=all&limit=100", headers=headers).json()
        candidate = next(m for m in result["candidates"] if m["id"] == candidate["id"])
        self.assertEqual(candidate["override_action"], "reject")
        self.assertGreaterEqual(len(candidate["audit"]), 2)
        excluded = self.client.get(path + "/matches?status=excluded&limit=100", headers=headers).json()["candidates"]
        low = next(m for m in excluded if not m["eligible"])
        promoted = self.client.post(path + f"/matches/{low['id']}/override", headers=headers,
            json=dict(action="promote", reason="Synthetic documented eligibility exception")).json()
        self.assertEqual(promoted["shortlist_status"], "shortlisted")
        self.assertFalse(promoted["eligible"])
        self.assertTrue(promoted["missing_requirements"])

    def test_new_table_rls_independently_and_fail_closed(self):
        models = (Company, Job, Match, MatchOverride)
        with tenant_session(2) as session:
            for model in models:
                rows = session.scalars(select(model)).all()  # Deliberately omit application filter in isolation test.
                self.assertTrue(rows)
                self.assertTrue(all(r.college_id == 2 for r in rows))
        with SessionLocal() as session:
            for model in models:
                self.assertEqual(session.scalars(select(model)).all(), [])
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname IN ('companies','jobs','matches','match_overrides')")).all()
            self.assertEqual(len(rows), 4)
            self.assertTrue(all(r.relrowsecurity and r.relforcerowsecurity for r in rows))
        for model in models:
            with self.subTest(table=model.__tablename__), self.assertRaises(DBAPIError):
                with tenant_session(1) as session:
                    row = session.scalar(select(model).where(model.college_id == 1))
                    # WITH CHECK must reject moving a row to another tenant.
                    session.execute(update(model).where(model.college_id == 1, model.id == row.id).values(college_id=2))

    def test_seed_companies_drives_and_idempotence(self):
        self.assertEqual(seed_students(), 0)
        self.assertEqual(seed_companies(), (0, []))
        with tenant_session(1) as session:
            count = session.scalar(select(func.count(Company.id)).where(Company.college_id == 1, Company.name.like("Synthetic Company %")))
            self.assertEqual(count, 12)
            for demo in DEMO_DRIVES:
                job = session.scalar(select(Job).where(Job.college_id == 1, Job.title == demo.title).order_by(Job.id))
                matches = session.scalars(select(Match).where(Match.college_id == 1, Match.job_id == job.id)).all()
                self.assertGreaterEqual(len(matches), 300)
                self.assertTrue(all(m.factor_breakdown and m.explanation for m in matches))

if __name__ == "__main__":
    unittest.main()
