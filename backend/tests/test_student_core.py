"""Run only against an isolated PostgreSQL test database, never production."""
import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import select, text, func
from sqlalchemy.exc import DBAPIError
from main import app
from auth import signing_secret, ISSUER, AUDIENCE
from database import engine, tenant_session, SessionLocal
from models import User, Student, StudentSkill, Project, Certification
from engines.readiness import calculate_readiness
from seed import seed_students

def sample_pdf():
    stream = b"BT /F1 12 Tf 50 750 Td (Synthetic resume: Python SQL student project.) Tj ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    result, offsets = b"%PDF-1.4\n", [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result += str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    position = len(result)
    result += b"xref\n0 6\n0000000000 65535 f \n"
    result += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return result + b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(position).encode() + b"\n%%EOF"

class StudentCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("127.0.0.1", "localhost"):
            raise RuntimeError("Tests require an explicitly approved localhost test database.")
        cls.client = TestClient(app)
        cls.client.__enter__()
        cls.accounts = []
        for college in (1, 1, 2):
            payload = {"name": "Integration Test", "email": f"{uuid.uuid4().hex}@test.jobjugaad.test",
                "password": "test-only-password-2026", "college_id": college}
            response = cls.client.post("/auth/signup", json=payload)
            assert response.status_code == 201, response.text
            result = response.json()
            cls.accounts.append((payload, result, {"Authorization": "Bearer " + result["access_token"]}))
        cls.payload = {"name": "Integration Test", "branch": "CSE", "cgpa": 8, "backlog_count": 0,
            "aptitude_score": 60, "communication_score": 70, "interview_score": 80,
            "skills": [{"skill_name": "Python", "proficiency": 80}, {"skill_name": "SQL", "proficiency": 60}],
            "projects": [{"title": "Coursework", "description": "A synthetic test project."}],
            "certifications": [{"title": "Course", "description": "Synthetic certificate."}]}
        for _, account, headers in cls.accounts:
            result = cls.client.put(f"/students/{account['user']['student_id']}", json=cls.payload, headers=headers)
            assert result.status_code == 200, result.text

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_login_claims_and_hash(self):
        payload, account, _ = self.accounts[0]
        response = self.client.post("/auth/login", json={k: v for k, v in payload.items() if k != "name"})
        self.assertEqual(response.status_code, 200)
        claims = jwt.decode(response.json()["access_token"], signing_secret(), algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE)
        self.assertEqual((claims["college_id"], claims["role"], claims["user_id"]), (1, "student", account["user"]["user_id"]))
        with tenant_session(1) as session:
            hashed = session.scalar(select(User.password_hash).where(User.id == claims["user_id"], User.college_id == 1))
            self.assertTrue(hashed.startswith("$2b$"))
        wrong = {k: v for k, v in payload.items() if k != "name"}
        wrong["password"] = "incorrect-password"
        self.assertEqual(self.client.post("/auth/login", json=wrong).status_code, 401)
        self.assertEqual(self.client.post("/auth/signup", json=payload).status_code, 409)

    def test_ownership_tenant_and_forged_identity(self):
        _, account, headers = self.accounts[0]
        own = account["user"]["student_id"]
        self.assertEqual(self.client.get(f"/students/{own}").status_code, 401)
        for other in self.accounts[1:]:
            other_id = other[1]["user"]["student_id"]
            for method, suffix, kwargs in [("get", "", {}), ("get", "/readiness", {}),
                ("put", "", {"json": self.payload}), ("post", "/resume", {"files": {"file": ("a.pdf", sample_pdf(), "application/pdf")}})]:
                self.assertEqual(getattr(self.client, method)(f"/students/{other_id}{suffix}", headers=headers, **kwargs).status_code, 404)
        token = account["access_token"]
        claims = jwt.decode(token, signing_secret(), algorithms=["HS256"], audience=AUDIENCE, issuer=ISSUER)
        for patch, expected in [({"exp": datetime.now(timezone.utc) - timedelta(seconds=5)}, 401), ({"role": "admin"}, 401)]:
            forged = jwt.encode({**claims, **patch}, signing_secret(), algorithm="HS256")
            self.assertEqual(self.client.get("/auth/me", headers={"Authorization": "Bearer " + forged}).status_code, expected)
        forged = jwt.encode(claims, "different-signing-secret-at-least-32-characters", algorithm="HS256")
        self.assertEqual(self.client.get("/auth/me", headers={"Authorization": "Bearer " + forged}).status_code, 401)
        self.assertEqual(self.client.post("/auth/signup", json={**self.accounts[0][0], "role": "admin"}).status_code, 422)
        self.assertEqual(self.client.put(f"/students/{own}", headers=headers, json={**self.payload, "college_id": 2}).status_code, 422)

    def test_rls_all_tables_without_application_filter(self):
        # Deliberately omit filters only here to independently prove the DB enforcement layer.
        models = (User, Student, StudentSkill, Project, Certification)
        with tenant_session(2) as session:
            for model in models:
                rows = session.scalars(select(model)).all()
                self.assertTrue(rows, model.__tablename__)
                self.assertTrue(all(row.college_id == 2 for row in rows))
        with SessionLocal() as session:
            for model in models:
                self.assertEqual(session.scalars(select(model)).all(), [])
        with engine.connect() as connection:
            policies = connection.execute(text("SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname IN ('users','students','student_skills','projects','certifications')")).all()
            self.assertEqual(len(policies), 5)
            self.assertTrue(all(row.relrowsecurity and row.relforcerowsecurity for row in policies))
        for model in models:
            with self.subTest(table=model.__tablename__), self.assertRaises(DBAPIError):
                with tenant_session(1) as session:
                    template = session.scalar(select(model).where(model.college_id == 1))
                    data = {column.name: getattr(template, column.name) for column in model.__table__.columns if column.name != "id"}
                    data["college_id"] = 2
                    if model is User:
                        data["email"] = uuid.uuid4().hex + "@test.example"
                    session.add(model(**data))
                    session.flush()
        with self.assertRaises(DBAPIError):
            with tenant_session(1) as session:
                session.add(Project(college_id=1, student_id=self.accounts[2][1]["user"]["student_id"], title="Invalid link", description="Must fail"))
                session.flush()

    def test_profile_and_resume_round_trip(self):
        _, account, headers = self.accounts[0]
        route = f"/students/{account['user']['student_id']}"
        result = self.client.get(route, headers=headers).json()
        score = result["readiness"]
        self.assertEqual(score["score"], 62)  # 21 + 5 + 12 + 9 + 7 + 8
        self.assertEqual(score["band"], "Developing")
        self.assertEqual(sum(row["contribution"] for row in score["breakdown"]), score["raw_score"])
        self.assertEqual(len(score["breakdown"]), 6)
        self.assertTrue(score["explanation"])
        self.assertEqual(self.client.get(route + "/readiness", headers=headers).json(), score)
        response = self.client.post(route + "/resume", headers=headers, files={"file": ("test.pdf", sample_pdf(), "application/pdf")})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("Synthetic resume", response.json()["profile"]["resume_text"])
        self.assertEqual(self.client.get(route, headers=headers).json()["resume_text"], response.json()["profile"]["resume_text"])
        for content, expected in [(b"not a pdf", 422), (b"%PDF-invalid", 422), (b"x" * (5 * 1024 * 1024 + 1), 413)]:
            self.assertEqual(self.client.post(route + "/resume", headers=headers, files={"file": ("bad.pdf", content, "application/pdf")}).status_code, expected)
        self.assertEqual(self.client.put(route, headers=headers, json={**self.payload, "cgpa": 11}).status_code, 422)

    def test_seed_idempotence_and_count(self):
        self.assertEqual(seed_students(), 0)
        with tenant_session(1) as session:
            count = session.scalar(select(func.count(User.id)).where(User.college_id == 1, User.email.like("student%@demo.jobjugaad.test")))
            self.assertEqual(count, 4796)

    def test_band_boundaries_missing_and_maximum(self):
        # Set all factors except projects to a chosen value and solve for total;
        # the boundary check uses the 80% remaining weight and zero projects.
        for desired, band in [(0,"Not Ready"),(40,"Not Ready"),(41,"Developing"),(65,"Developing"),(66,"Ready")]:
            value = desired / .8
            student = SimpleNamespace(cgpa=value / 10, aptitude_score=value, communication_score=value, interview_score=value)
            score = calculate_readiness(student, [SimpleNamespace(proficiency=value)], [])
            self.assertEqual((score.score, score.band), (desired, band))
        for desired, band in [(85,"Ready"), (86,"Highly Employable"), (100,"Highly Employable")]:
            value = (desired - 20) / .8
            student = SimpleNamespace(cgpa=value / 10, aptitude_score=value, communication_score=value, interview_score=value)
            score = calculate_readiness(student, [SimpleNamespace(proficiency=value)], [1,2,3,4,5])
            self.assertEqual((score.score, score.band), (desired, band))
        absent = SimpleNamespace(cgpa=None, aptitude_score=None, communication_score=None, interview_score=None)
        self.assertTrue(all(f.missing for f in calculate_readiness(absent, [], []).breakdown))

if __name__ == "__main__":
    unittest.main(verbosity=2)
