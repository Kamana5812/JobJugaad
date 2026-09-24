"""Public model integration and real PostgreSQL tenant/ownership checks."""
import os
import unittest
import uuid
from unittest.mock import patch
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from database import engine, initialize_schema, tenant_session, SessionLocal
from models import PlacementModelProfile
from schemas import PlacementModelInput
from engines import placement_model as model
from main import app

class PlacementExplanationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model.load_model()
        cls.data = pd.read_csv(model.DIRECTORY.parent / "data" / "Placement_Data_Full_Class.csv")

    def test_all_public_rows_reconcile_with_saved_forest(self):
        self.assertEqual(model.model_status(), "ready")
        features = self.data.drop(columns=["sl_no", "status", "salary"])
        expected = model._pipeline.predict_proba(features)[:, 1] * 100
        for index, values in enumerate(features.to_dict("records")):
            signal = model.predict_signal(PlacementModelInput(**values))
            self.assertTrue(signal["available"])
            self.assertEqual(len(signal["breakdown"]), 12)
            self.assertAlmostEqual(signal["score"], expected[index], places=9)
            self.assertAlmostEqual(signal["baseline"] + sum(f["contribution"] for f in signal["breakdown"]), signal["score"], places=9)
            self.assertIn("not your probability", signal["explanation"])
        # Requests and repeated startup calls must neither fit nor reload a model.
        with patch("joblib.load", side_effect=AssertionError("Reloaded")), patch.object(model._pipeline, "fit", side_effect=AssertionError("Retrained")):
            model.load_model()
            model.predict_signal(PlacementModelInput(**features.iloc[0].to_dict()))

    def test_missing_inputs_and_failed_load_never_invent_score(self):
        signal = model.predict_signal(PlacementModelInput(ssc_p=80))
        self.assertFalse(signal["available"])
        self.assertNotIn("score", signal)
        self.assertIn("mba_p", signal["missing_fields"])
        values = self.data.drop(columns=["sl_no", "status", "salary"]).iloc[0].to_dict()
        with patch.object(model, "_pipeline", None):
            self.assertFalse(model.predict_signal(PlacementModelInput(**values))["available"])
        # Bad trusted-artifact checksum must fail before attempting deserialization.
        with patch.object(model, "_attempted", False), patch.object(model, "_pipeline", None), patch.object(model, "_report", None), patch("hashlib.sha256") as checksum, patch("joblib.load") as loader:
            checksum.return_value.hexdigest.return_value = "wrong"
            model.load_model()
            loader.assert_not_called()
            self.assertEqual(model.model_status(), "unavailable")

class PlacementApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("localhost", "127.0.0.1"):
            raise RuntimeError("An explicitly approved local test database is required.")
        initialize_schema()
        model.load_model()
        cls.client = TestClient(app)
        cls.accounts = []
        for college in (1, 1, 2):
            response = cls.client.post("/auth/signup", json={"name": "Model Integration Test",
                "email": uuid.uuid4().hex + "@test.jobjugaad.test", "password": "test-model-password-2026", "college_id": college})
            assert response.status_code == 201, response.text
            data = response.json()
            cls.accounts.append((data["user"]["student_id"], {"Authorization": "Bearer " + data["access_token"]}))
        cls.inputs = pd.read_csv(model.DIRECTORY.parent / "data" / "Placement_Data_Full_Class.csv").drop(columns=["sl_no", "status", "salary"]).iloc[0].to_dict()

    def test_contract_roundtrip_and_readiness_independence(self):
        student_id, headers = self.accounts[0]
        route = f"/students/{student_id}"
        before = self.client.get(route + "/readiness", headers=headers).json()
        self.client.put(route + "/placement-model", headers=headers, json={})
        initial = self.client.get(route + "/placement-model", headers=headers).json()
        self.assertFalse(initial["signal"]["available"])
        response = self.client.put(route + "/placement-model", headers=headers, json=self.inputs)
        self.assertEqual(response.status_code, 200, response.text)
        saved = response.json()
        self.assertTrue(saved["signal"]["available"])
        self.assertEqual(saved["evaluation"]["confusion_matrix"], [[11, 2], [3, 27]])
        self.assertEqual(self.client.get(route + "/placement-model", headers=headers).json(), saved)
        self.assertEqual(self.client.get(route + "/readiness", headers=headers).json(), before)
        for invalid in ({"salary": 200000}, {"gender": "Other"}, {"degree_p": 101}, {"college_id": 2}, {"ssc_p": "nan"}):
            self.assertEqual(self.client.put(route + "/placement-model", headers=headers, json=self.inputs | invalid).status_code, 422)
        # A student can clear the optional evidence; the old score must disappear.
        self.assertFalse(self.client.put(route + "/placement-model", headers=headers, json={}).json()["signal"]["available"])
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/students/{student_id}/placement-model", schema["paths"])

    def test_api_and_rls_read_write_isolation(self):
        own_id, headers = self.accounts[0]
        for student_id, _ in self.accounts[1:]:
            for method in ("get", "put"):
                kwargs = {"json": self.inputs} if method == "put" else {}
                self.assertEqual(getattr(self.client, method)(f"/students/{student_id}/placement-model", headers=headers, **kwargs).status_code, 404)
        self.assertEqual(self.client.get(f"/students/{own_id}/placement-model").status_code, 401)
        for student_id, auth in self.accounts:
            self.assertEqual(self.client.put(f"/students/{student_id}/placement-model", headers=auth, json=self.inputs).status_code, 200)
        # Omit application filters deliberately in security tests to exercise RLS itself.
        with tenant_session(2) as session:
            rows = session.scalars(select(PlacementModelProfile)).all()
            self.assertTrue(rows)
            self.assertTrue(all(row.college_id == 2 for row in rows))
        with SessionLocal() as session:
            self.assertEqual(session.scalars(select(PlacementModelProfile)).all(), [])
        with self.assertRaises(DBAPIError), tenant_session(1) as session:
            session.add(PlacementModelProfile(student_id=self.accounts[2][0], college_id=2, inputs=self.inputs))
            session.flush()
        with self.assertRaises(DBAPIError), tenant_session(1) as session:
            session.add(PlacementModelProfile(student_id=self.accounts[2][0], college_id=1, inputs=self.inputs))
            session.flush()
        with tenant_session(1) as session:
            statement = PlacementModelProfile.__table__.update().where(PlacementModelProfile.student_id == self.accounts[2][0]).values(inputs={})
            self.assertEqual(session.execute(statement).rowcount, 0)
