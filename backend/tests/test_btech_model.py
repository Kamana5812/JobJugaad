"""Engineering model reproduction, explanations and PostgreSQL protection."""
import json
import os
import unittest
import uuid
from unittest.mock import patch
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from database import engine, initialize_schema, tenant_session, SessionLocal
from models import BTechModelProfile
from schemas import BTechModelInput
from engines import btech_model as model
from ml.engineering.train_model import load_dataset, split_dataset, FEATURES, sha256, HERE
from main import app

class EngineeringModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model.load_model()
        cls.data=load_dataset()
        cls.report=json.loads((HERE/"evaluation_report.json").read_text(encoding="utf-8"))

    def test_source_group_split_and_measured_report(self):
        train,test,groups=split_dataset(self.data)
        self.assertEqual((len(train),len(test),len(set(groups))),(2374,592,181))
        self.assertFalse(set(groups[train]) & set(groups[test]))
        self.assertEqual(self.report["train_row_numbers"],[int(i)+1 for i in train])
        self.assertEqual(self.report["test_row_numbers"],[int(i)+1 for i in test])
        self.assertEqual(sha256(HERE/"training_protocol.json"),self.report["protocol_sha256"])
        self.assertEqual(list(model._pipeline.feature_names_in_),FEATURES)
        prediction=model._pipeline.predict(self.data.iloc[test][FEATURES])
        labels=self.data.iloc[test].PlacedOrNot
        for key,fn in [("accuracy",accuracy_score),("precision",precision_score),("recall",recall_score),("f1",f1_score)]:
            self.assertEqual(fn(labels,prediction),self.report["metrics"][key])
        self.assertEqual(confusion_matrix(labels,prediction,labels=[0,1]).tolist(),[[257,8],[87,240]])
        self.assertEqual(prediction.tolist(),[p["predicted"] for p in self.report["held_out_predictions"]])
        encoder=model._pipeline.named_steps["preprocess"].named_transformers_["categorical"]
        self.assertEqual(set(encoder.categories_[0]),set(self.data.iloc[train].Stream))
        self.assertFalse(set(FEATURES)&{"Age","Gender","Hostel","PlacedOrNot"})

    def test_every_distinct_profile_explains_actual_forest_output(self):
        profiles=self.data[FEATURES].drop_duplicates()
        expected=model._pipeline.predict_proba(profiles)[:,1]*100
        for index,row in enumerate(profiles.to_dict("records")):
            inputs=BTechModelInput(**{key:row[source] for key,source in model.KEYS.items()})
            signal=model.predict_signal(inputs)
            self.assertTrue(signal["available"])
            self.assertEqual(len(signal["breakdown"]),4)
            self.assertAlmostEqual(signal["score"],expected[index],places=9)
            self.assertAlmostEqual(signal["baseline"]+sum(f["contribution"] for f in signal["breakdown"]),signal["score"],places=9)
            self.assertIn("not your probability",signal["explanation"])
        with patch("joblib.load",side_effect=AssertionError("Reload")),patch.object(model._pipeline,"fit",side_effect=AssertionError("Retrain")):
            model.load_model()
            model.predict_signal(inputs)

    def test_missing_outside_source_and_bad_artifact(self):
        self.assertFalse(model.predict_signal(BTechModelInput())["available"])
        valid={"cgpa":8,"stream":"Computer Science","internships":1,"history_of_backlogs":0}
        for change in ({"cgpa":9.5},{"cgpa":4.9},{"internships":4}):
            signal=model.predict_signal(BTechModelInput(**(valid|change)))
            self.assertFalse(signal["available"])
            self.assertIn("outside",signal["explanation"])
        with patch.object(model,"_attempted",False),patch.object(model,"_pipeline",None),patch.object(model,"_report",None),patch("hashlib.sha256") as checksum,patch("joblib.load") as loader:
            checksum.return_value.hexdigest.return_value="wrong"
            model.load_model()
            loader.assert_not_called()
            self.assertEqual(model.model_status(),"unavailable")
            self.assertFalse(model.predict_signal(BTechModelInput(**valid))["available"])

class EngineeringApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE")!="yes" or engine.url.host not in ("localhost","127.0.0.1"):
            raise RuntimeError("Use an explicitly allowed local test database")
        initialize_schema();model.load_model()
        cls.client=TestClient(app)
        cls.accounts=[]
        for college in (1,1,2):
            response=cls.client.post("/auth/signup",json={"name":"BTech Synthetic Test","email":uuid.uuid4().hex+"@test.jobjugaad.test","password":"btech-test-only-password","college_id":college})
            assert response.status_code==201
            data=response.json();cls.accounts.append((data["user"]["student_id"],{"Authorization":"Bearer "+data["access_token"]}))
        cls.payload={"cgpa":8,"stream":"Computer Science","internships":1,"history_of_backlogs":0}

    def test_roundtrip_no_mba_and_no_change_to_other_scores(self):
        student,headers=self.accounts[0];base=f"/students/{student}"
        before=self.client.get(base+"/readiness",headers=headers).json()
        mba=self.client.get(base+"/placement-model",headers=headers).json()
        response=self.client.put(base+"/btech-placement-model",headers=headers,json=self.payload)
        self.assertEqual(response.status_code,200,response.text)
        result=response.json();self.assertTrue(result["signal"]["available"])
        self.assertEqual(self.client.get(base+"/btech-placement-model",headers=headers).json(),result)
        self.assertEqual(self.client.get(base+"/readiness",headers=headers).json(),before)
        self.assertEqual(self.client.get(base+"/placement-model",headers=headers).json(),mba)
        for invalid in ({"mba_p":70},{"gender":"Male"},{"college_id":2},{"history_of_backlogs":2},{"internships":1.5},{"stream":"Other"},{"cgpa":"NaN"}):
            self.assertEqual(self.client.put(base+"/btech-placement-model",headers=headers,json=self.payload|invalid).status_code,422)
        outside=self.client.put(base+"/btech-placement-model",headers=headers,json=self.payload|{"cgpa":9.5}).json()
        self.assertEqual(outside["inputs"]["cgpa"],9.5)
        self.assertFalse(outside["signal"]["available"])
        cleared=self.client.put(base+"/btech-placement-model",headers=headers,json={}).json()
        self.assertIsNone(cleared["signal"]["score"])
        self.assertIn(base.replace(str(student),"{student_id}")+"/btech-placement-model",self.client.get('/openapi.json').json()['paths'])

    def test_api_ownership_and_independent_rls(self):
        own,headers=self.accounts[0]
        for student,auth in self.accounts:
            self.assertEqual(self.client.put(f"/students/{student}/btech-placement-model",headers=auth,json=self.payload).status_code,200)
        self.assertEqual(self.client.get(f"/students/{own}/btech-placement-model").status_code,401)
        for student,_ in self.accounts[1:]:
            for method in ("get","put"):
                kwargs={"json":self.payload} if method=="put" else {}
                self.assertEqual(getattr(self.client,method)(f"/students/{student}/btech-placement-model",headers=headers,**kwargs).status_code,404)
        # Deliberately omit college filters only here to test the database boundary.
        with tenant_session(2) as session:
            rows=session.scalars(select(BTechModelProfile)).all()
            self.assertTrue(rows);self.assertTrue(all(r.college_id==2 for r in rows))
        with SessionLocal() as session:
            self.assertEqual(session.scalars(select(BTechModelProfile)).all(),[])
        for college in (1,2):
            with self.assertRaises(DBAPIError),tenant_session(1) as session:
                session.add(BTechModelProfile(student_id=self.accounts[2][0],college_id=college,inputs=self.payload));session.flush()
        with tenant_session(1) as session:
            result=session.execute(BTechModelProfile.__table__.update().where(BTechModelProfile.student_id==self.accounts[2][0]).values(inputs={}))
            self.assertEqual(result.rowcount,0)
