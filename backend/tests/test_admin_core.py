"""Scheduling and support correctness checks; integration runs only on localhost."""
import json
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as Obj
from fastapi.testclient import TestClient
from sqlalchemy import select, update, text
from sqlalchemy.exc import DBAPIError
from main import app
from admin_access import provision_admin_accounts
from database import engine, tenant_session, SessionLocal
from models import Schedule, Interview, ScheduleEvent, RiskPrediction, SupportReview, Student, Job
from schemas import ScheduleInput
from engines.scheduler import propose_slot
from engines.risk import evaluate_support
from seed import seed_phase3


class SchedulingRuleTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2035,1,1,10,tzinfo=timezone.utc)
        self.slot = ScheduleInput(job_id=1,student_id=1,scheduled_time=self.start,
            duration_minutes=30,venue="Hall A",panel_id="Panel A")

    def booking(self, identity, start, end, **values):
        return Obj(id=identity,job_id=2,student_id=9,venue="other",panel_id="other",status="scheduled",
            scheduled_time=self.start+timedelta(minutes=start),end_time=self.start+timedelta(minutes=end),**values)

    def test_chained_constraints_and_cross_drive_explanation(self):
        a=self.booking(1,0,30);a.student_id=1
        b=self.booking(2,30,60);b.venue="hall a"
        c=self.booking(3,60,90);c.panel_id="panel a"
        result=propose_slot(self.slot,[a,b,c])
        self.assertEqual(result.proposed_time,self.start+timedelta(minutes=90))
        self.assertEqual({kind for item in result.conflicts for kind in item.kinds},
            {"student","venue","panel","overlapping_drive"})
        self.assertTrue(result.requires_approval)
        self.assertEqual(self.slot.scheduled_time,self.start)

    def test_adjacent_intervals_independent_drives_and_cancelled(self):
        a=self.booking(1,-30,0);a.student_id=1
        b=self.booking(2,30,60);b.venue="hall a"
        independent=self.booking(3,0,30)
        cancelled=self.booking(4,0,30);cancelled.status="cancelled";cancelled.student_id=1
        self.assertEqual(propose_slot(self.slot,[a,b,independent,cancelled]).conflicts,[])
        with self.assertRaises(ValueError):
            ScheduleInput(job_id=1,student_id=1,scheduled_time="2035-01-01T10:00:00",venue="a",panel_id="a")

    def test_search_bound_and_reschedule_exclusion(self):
        blocker=self.booking(1,0,8*24*60);blocker.student_id=1
        self.assertIsNone(propose_slot(self.slot,[blocker]).proposed_time)
        self.slot.reschedule_interview_id=1
        self.assertEqual(propose_slot(self.slot,[blocker]).proposed_time,self.start)


class SupportRuleTests(unittest.TestCase):
    def test_and_thresholds_unknowns_and_explanations(self):
        student=Obj(interview_score=39)
        job=Obj(title="Synthetic role",required_skills=[dict(skill_name=s,min_proficiency=60) for s in ("python","sql","aws","git")])
        skills=[Obj(skill_name="python",proficiency=80)]
        result=evaluate_support(student,skills,job,1)
        self.assertTrue(result.flagged)
        self.assertEqual(result.score,3)
        self.assertEqual(sum(f.contribution for f in result.contributing_factors),3)
        self.assertEqual(len(result.recommendation),3)
        self.assertTrue(all(f.explanation for f in result.contributing_factors))
        self.assertFalse(evaluate_support(student,skills,job,2).flagged)
        student.interview_score=40
        self.assertFalse(evaluate_support(student,skills,job,1).flagged)
        student.interview_score=None
        result=evaluate_support(student,skills,job,0)
        self.assertFalse(result.flagged)
        self.assertFalse(result.assessable)
        self.assertIn("missing",result.explanation)
        self.assertNotIn("confidence",result.model_dump())


class AdminIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("localhost","127.0.0.1"):
            raise RuntimeError("Explicit localhost test database required.")
        cls.old_admins=os.environ.get("ADMIN_ACCOUNTS")
        os.environ["ADMIN_ACCOUNTS"]="[]"
        cls.client=TestClient(app);cls.client.__enter__()
        cls.accounts=[]
        cls.suffix=uuid.uuid4().hex[:12]
        cls.start=datetime(2035,1,1,10,tzinfo=timezone.utc)+timedelta(days=int(cls.suffix[:4],16))
        for college in (1,2):
            credentials=dict(email=f"admin-{cls.suffix}-{college}@test.example",password="Synthetic-only-2026",college_id=college)
            result=cls.client.post("/auth/signup",json={**credentials,"name":"Synthetic Admin"}).json()
            cls.accounts.append(dict(credentials=credentials,student_id=result["user"]["student_id"],old_token=result["access_token"]))
        os.environ["ADMIN_ACCOUNTS"]=json.dumps([dict(email=a["credentials"]["email"],college_id=a["credentials"]["college_id"]) for a in cls.accounts])
        assert provision_admin_accounts()==2
        for account in cls.accounts:
            credentials=account["credentials"];college=credentials["college_id"]
            login=cls.client.post("/auth/login",json=credentials)
            assert login.status_code==200,login.text
            account["headers"]={"Authorization":"Bearer "+login.json()["access_token"]}
            r=cls.client.post("/auth/recruiter/signup",json=dict(email=f"recruiter-{cls.suffix}-{college}@test.example",
                password="Synthetic-only-2026",college_id=college,company=dict(name="Synthetic Calendar Company",industry="Testing"))).json()
            account["recruiter_headers"]={"Authorization":"Bearer "+r["access_token"]}
            job=cls.client.post("/recruiters/jobs",headers=account["recruiter_headers"],json=dict(title="Synthetic four-skill role",
                ctc=5,min_cgpa=5,eligible_branches=["CSE"],required_skills=[dict(skill_name=s,min_proficiency=60) for s in ("python","sql","aws","git")]))
            assert job.status_code==201,job.text
            account["job_id"]=job.json()["id"]
            student=cls.client.post("/auth/signup",json=dict(email=f"support-{cls.suffix}-{college}@test.example",
                password="Synthetic-only-2026",college_id=college,name="Synthetic Flag Example")).json()
            account["support_student_id"]=student["user"]["student_id"]
            account["student_headers"]={"Authorization":"Bearer "+student["access_token"]}
            cls.client.put(f"/students/{account['support_student_id']}",headers=account["student_headers"],
                json=dict(name="Synthetic Flag Example",branch="CSE",cgpa=6,interview_score=25,skills=[]))
            slot=dict(job_id=account["job_id"],student_id=account["student_id"],scheduled_time=cls.start.isoformat(),
                duration_minutes=30,venue="test-"+cls.suffix,panel_id="panel-"+cls.suffix)
            created=cls.client.post("/admin/schedules",headers=account["headers"],json=slot)
            assert created.status_code==201,created.text
            account["slot"]=slot;account["proposal"]=created.json()
            review=cls.client.post(f"/admin/schedules/{created.json()['id']}/review",headers=account["headers"],
                json=dict(action="approve",version=1,reason="Synthetic baseline confirmation"))
            assert review.status_code==200,review.text
            result=cls.client.post("/admin/support/run",headers=account["headers"],json=dict(job_id=account["job_id"]))
            assert result.status_code==200,result.text
            flagged=next(s for s in result.json()["students"] if s["student_id"]==account["support_student_id"])
            account["prediction_id"]=flagged["id"]
            assert cls.client.post(f"/admin/support/{flagged['id']}/review",headers=account["headers"],
                json=dict(action="reviewed",reason="Synthetic support evidence reviewed")).status_code==200

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None,None,None)
        if cls.old_admins is None:os.environ.pop("ADMIN_ACCOUNTS",None)
        else:os.environ["ADMIN_ACCOUNTS"]=cls.old_admins

    def test_interview_notification_delivery_and_recipient_isolation(self):
        account = self.accounts[0]
        # Target the baseline interview: earlier tests may confirm another booking.
        board = self.client.get("/admin/schedules", headers=account["headers"]).json()
        baseline = next(row for row in board["interviews"] if row["schedule_id"] == account["proposal"]["id"])
        feed = self.client.get("/notifications", headers=account["headers"])
        self.assertEqual(feed.status_code, 200, feed.text)
        confirmed = [item for item in feed.json()["notifications"]
            if item["title"] == "Interview confirmed" and item["body"].startswith(f"Interview #{baseline['id']} for drive #{account['job_id']} ")]
        self.assertEqual(len(confirmed), 1)
        notice = confirmed[0]
        self.assertEqual(notice["delivery"], "simulated_in_app")
        self.assertIn(account["slot"]["venue"], notice["body"])
        self.assertEqual(self.client.put(f"/notifications/{notice['id']}/read", headers=account["student_headers"]).status_code, 404)
        self.assertEqual(self.client.put(f"/notifications/{notice['id']}/read", headers=self.accounts[1]["headers"]).status_code, 404)
        read = self.client.put(f"/notifications/{notice['id']}/read", headers=account["headers"])
        self.assertEqual(read.status_code, 200, read.text)
        self.assertIsNotNone(read.json()["read_at"])

    def test_admin_role_allowlist_and_cross_tenant_access(self):
        a,b=self.accounts
        self.assertEqual(self.client.get("/admin/schedules").status_code,401)
        for headers in (a["student_headers"],a["recruiter_headers"]):
            self.assertEqual(self.client.get("/admin/analytics/overview",headers=headers).status_code,403)
            self.assertEqual(self.client.post("/admin/support/run",headers=headers,json=dict(job_id=a["job_id"])).status_code,403)
        self.assertEqual(self.client.get("/auth/me",headers={"Authorization":"Bearer "+a["old_token"]}).status_code,401)
        self.assertEqual(self.client.post("/admin/schedules",headers=a["headers"],json={**a["slot"],"student_id":b["student_id"]}).status_code,404)
        self.assertEqual(self.client.get("/admin/support",headers=a["headers"],params=dict(job_id=b["job_id"])).status_code,404)
        self.assertEqual(self.client.post(f"/admin/support/{b['prediction_id']}/review",headers=a["headers"],
            json=dict(action="dismissed",reason="Wrong college must be blocked")).status_code,404)
        previous=os.environ["ADMIN_ACCOUNTS"];os.environ["ADMIN_ACCOUNTS"]="[]"
        try:self.assertEqual(self.client.get("/admin/schedules",headers=a["headers"]).status_code,403)
        finally:os.environ["ADMIN_ACCOUNTS"]=previous

    def test_preview_pending_approval_and_reschedule_audit(self):
        a=self.accounts[0];headers=a["headers"]
        preview=self.client.post("/admin/schedules/check-conflict",headers=headers,json=a["slot"]).json()
        self.assertTrue(preview["conflicts"])
        self.assertEqual(datetime.fromisoformat(preview["proposed_time"].replace("Z","+00:00")),self.start+timedelta(minutes=30))
        board=self.client.get("/admin/schedules",headers=headers).json()
        original=next(i for i in board["interviews"] if i["schedule_id"]==a["proposal"]["id"])
        payload={**a["slot"],"scheduled_time":(self.start+timedelta(hours=3)).isoformat(),"reschedule_interview_id":original["id"]}
        proposed=self.client.post("/admin/schedules",headers=headers,json=payload).json()
        self.assertEqual(proposed["status"],"pending")
        unchanged=self.client.get("/admin/schedules",headers=headers).json()
        self.assertEqual(next(i for i in unchanged["interviews"] if i["id"]==original["id"])["status"],"scheduled")
        result=self.client.post(f"/admin/schedules/{proposed['id']}/review",headers=headers,
            json=dict(action="approve",version=proposed["version"],reason="Synthetic reschedule approved"))
        self.assertEqual(result.status_code,200,result.text)
        board=self.client.get("/admin/schedules",headers=headers).json()
        self.assertEqual(next(i for i in board["interviews"] if i["id"]==original["id"])["status"],"cancelled")
        self.assertTrue(any(e["action"]=="approve" and e["reason"]=="Synthetic reschedule approved" for e in board["audit"]))

    def test_concurrent_approval_recheck_and_stale_version(self):
        a=self.accounts[0];headers=a["headers"]
        payload={**a["slot"],"scheduled_time":(self.start+timedelta(days=1)).isoformat()}
        proposals=[self.client.post("/admin/schedules",headers=headers,json=payload).json() for _ in range(2)]
        def approve(p):
            return self.client.post(f"/admin/schedules/{p['id']}/review",headers=headers,json=dict(action="approve",version=1,reason="Concurrent synthetic approval"))
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses=list(pool.map(approve,proposals))
        self.assertEqual(sorted(r.status_code for r in responses),[200,409])
        loser=proposals[next(i for i,r in enumerate(responses) if r.status_code==409)]
        recheck=self.client.post(f"/admin/schedules/{loser['id']}/recheck",headers=headers,json=dict(version=1))
        self.assertEqual(recheck.status_code,200,recheck.text)
        revised=recheck.json()
        self.assertEqual(revised["version"],2)
        self.assertEqual(approve(loser).status_code,409)
        reject=self.client.post(f"/admin/schedules/{loser['id']}/review",headers=headers,
            json=dict(action="reject",version=2,reason="Synthetic reviewer rejected the alternative"))
        self.assertEqual(reject.status_code,200)

    def test_support_review_preservation_and_reopen_on_changed_evidence(self):
        a=self.accounts[0];headers=a["headers"]
        result=self.client.post("/admin/support/run",headers=headers,json=dict(job_id=a["job_id"])).json()
        row=next(s for s in result["students"] if s["student_id"]==a["support_student_id"])
        self.assertEqual(row["review_status"],"reviewed")
        self.assertTrue(row["contributing_factors"] and row["recommendation"] and row["explanation"])
        self.assertTrue(row["audit"][0]["snapshot"]["contributing_factors"])
        self.client.put(f"/students/{a['support_student_id']}",headers=a["student_headers"],
            json=dict(name="Synthetic Flag Example",branch="CSE",cgpa=6,interview_score=20,skills=[]))
        result=self.client.post("/admin/support/run",headers=headers,json=dict(job_id=a["job_id"])).json()
        row=next(s for s in result["students"] if s["student_id"]==a["support_student_id"])
        self.assertEqual(row["review_status"],"active")

    def test_rls_all_new_tables_without_app_filters(self):
        models=(Schedule,Interview,ScheduleEvent,RiskPrediction,SupportReview)
        with tenant_session(2) as session:
            for model in models:
                rows=session.scalars(select(model)).all()  # Intentionally omit filters only for RLS verification.
                self.assertTrue(rows,model.__tablename__)
                self.assertTrue(all(r.college_id==2 for r in rows))
        with SessionLocal() as session:
            for model in models:self.assertEqual(session.scalars(select(model)).all(),[])
        with engine.connect() as conn:
            policies=conn.execute(text("SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('schedules','interviews','schedule_events','risk_predictions','support_reviews')")).all()
            self.assertEqual(len(policies),5)
            self.assertTrue(all(p.relrowsecurity and p.relforcerowsecurity for p in policies))
        for model in models:
            with self.subTest(table=model.__tablename__),self.assertRaises(DBAPIError):
                with tenant_session(1) as session:
                    row=session.scalar(select(model).where(model.college_id==1))
                    session.execute(update(model).where(model.id==row.id,model.college_id==1).values(college_id=2))
        with self.assertRaises(DBAPIError):
            with tenant_session(1) as session:
                row=session.scalar(select(Interview).where(Interview.college_id==1))
                session.add(Interview(college_id=1,job_id=self.accounts[1]["job_id"],student_id=row.student_id,
                    scheduled_time=self.start,end_time=self.start+timedelta(minutes=30),venue="invalid",panel_id="invalid"))

    def test_interview_status_and_documented_endpoints(self):
        a,b=self.accounts;headers=a["headers"]
        self.assertEqual(self.client.get("/docs").status_code,200)
        paths=self.client.get("/openapi.json").json()["paths"]
        self.assertEqual(sum(len([m for m in methods if m in ("get","post","put")]) for path,methods in paths.items() if path.startswith("/admin/")),14)
        payload={**a["slot"],"scheduled_time":(self.start+timedelta(days=30)).isoformat()}
        proposal=self.client.post("/admin/schedules",headers=headers,json=payload).json()
        approved=self.client.post(f"/admin/schedules/{proposal['id']}/review",headers=headers,
            json=dict(action="approve",version=1,reason="Synthetic status test booking"))
        self.assertEqual(approved.status_code,200)
        board=self.client.get("/admin/schedules",headers=headers).json()
        item=next(i for i in board["interviews"] if i["schedule_id"]==proposal["id"])
        route=f"/admin/interviews/{item['id']}/status"
        change=dict(status="completed",reason="Synthetic outcome status test")
        self.assertEqual(self.client.put(route,headers=b["headers"],json=change).status_code,404)
        self.assertEqual(self.client.put(route,headers=headers,json=change).status_code,422)
        self.assertEqual(self.client.put(route,headers=headers,json={**change,"status":"cancelled"}).status_code,200)
        self.assertEqual(self.client.put(route,headers=headers,json=change).status_code,409)
        with tenant_session(1) as session:
            past=datetime.now(timezone.utc)-timedelta(days=2)
            item=Interview(college_id=1,job_id=a["job_id"],student_id=a["student_id"],
                scheduled_time=past,end_time=past+timedelta(minutes=30),venue="past-test",panel_id=self.suffix,status="scheduled")
            session.add(item);session.flush();identity=item.id
        completed=self.client.put(f"/admin/interviews/{identity}/status",headers=headers,json=change)
        self.assertEqual(completed.status_code,200,completed.text)
        self.assertEqual(completed.json()["status"],"completed")
        board=self.client.get("/admin/schedules",headers=headers).json()
        self.assertTrue(any(e["action"]=="interview_status" and e["snapshot"]["after"]["id"]==identity for e in board["audit"]))

    def test_analytics_and_seed_idempotence(self):
        headers=self.accounts[0]["headers"]
        result=self.client.get("/admin/analytics/overview",headers=headers).json()
        self.assertIsNotNone(result["placement_percent"])
        self.assertIn("accepted offer",result["placement_explanation"])
        self.assertTrue(result["branch_conversion"] and result["skill_conversion"])
        for row in result["branch_conversion"]+result["skill_conversion"]:
            self.assertLessEqual(row["shortlisted_students"],row["total_students"])
        created=seed_phase3()
        self.assertEqual(created["support_students"],0)
        self.assertEqual(created["interviews"],0)
        with tenant_session(1) as session:
            fixture=session.scalars(select(Interview).where(Interview.college_id==1,Interview.seed_key.in_(["phase3-double-booking-a","phase3-double-booking-b"]))).all()
            self.assertEqual(len(fixture),2)
            self.assertLess(max(i.scheduled_time for i in fixture),min(i.end_time for i in fixture))

if __name__=="__main__":
    unittest.main()
