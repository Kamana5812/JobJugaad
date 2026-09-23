"""Phase 4 PostgreSQL workflow checks; never run against the live database."""
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from sqlalchemy import select,update,text
from sqlalchemy.exc import DBAPIError
import test_admin_core as admin_tests
from database import tenant_session,SessionLocal,engine
from models import Interview,Offer,OfferEvent,Notification

class OfferCoreTests(unittest.TestCase):
    setUpClass=classmethod(admin_tests.AdminIntegrationTests.setUpClass.__func__)
    tearDownClass=classmethod(admin_tests.AdminIntegrationTests.tearDownClass.__func__)

    def setUp(self):
        self.rows=[]
        for account in self.accounts:
            college=account["credentials"]["college_id"]
            job=self.client.post("/recruiters/jobs",headers=account["recruiter_headers"],json=dict(
                title="Synthetic offer workflow",ctc=7.5,min_cgpa=4,eligible_branches=["CSE"],
                required_skills=[dict(skill_name="python",min_proficiency=30)]))
            self.assertEqual(job.status_code,201,job.text)
            with tenant_session(college) as session:
                past=datetime.now(timezone.utc)-timedelta(days=1)
                row=Interview(college_id=college,job_id=job.json()["id"],student_id=account["support_student_id"],
                    scheduled_time=past,end_time=past+timedelta(minutes=30),venue="offer-test",panel_id=self.suffix,status="selected")
                session.add(row);session.flush();identity=row.id
            created=self.client.post("/admin/offers",headers=account["headers"],
                json=dict(interview_id=identity,reason="Synthetic selected interview offer"))
            self.assertEqual(created.status_code,201,created.text)
            self.rows.append(created.json())

    def admin_change(self,row,stage,value,account=0,expected=200):
        result=self.client.put(f"/admin/offers/{row['id']}",headers=self.accounts[account]["headers"],
            json=dict(stage=stage,value=value,version=row["version"],reason="Synthetic stage review and evidence"))
        self.assertEqual(result.status_code,expected,result.text)
        return result.json()

    def student_change(self,row,action,account=0,expected=200):
        identity=self.accounts[account]["support_student_id"]
        result=self.client.post(f"/students/{identity}/offers/{row['id']}/actions",headers=self.accounts[account]["student_headers"],
            json=dict(action=action,version=row["version"],reason="Synthetic student confirms this action"))
        self.assertEqual(result.status_code,expected,result.text)
        return result.json()

    def test_complete_lifecycle_audit_notification_and_analytics(self):
        row=self.rows[0]
        self.student_change(row,"accept",expected=409)
        self.admin_change(row,"joining_status","joined",expected=409)
        row=self.admin_change(row,"offer_letter_status","issued")
        row=self.student_change(row,"accept")
        self.assertEqual(row["verification_status"],"pending")
        self.admin_change(row,"verification_status","verified",expected=409)
        row=self.student_change(row,"submit_documents")
        row=self.admin_change(row,"verification_status","verified")
        row=self.admin_change(row,"joining_status","joined")
        self.assertEqual(len(row["audit"]),6)
        self.assertEqual(row["audit"][-1]["snapshot"]["before"]["joining_status"],"pending")
        self.assertEqual(row["audit"][-1]["snapshot"]["after"]["joining_status"],"joined")
        self.assertTrue(row["next_steps"] and row["methodology"])
        self.student_change(row,"decline",expected=409)
        analytics=self.client.get("/admin/analytics/overview",headers=self.accounts[0]["headers"]).json()
        self.assertGreaterEqual(analytics["accepted_students"],1)
        self.assertGreaterEqual(analytics["joined_students"],1)
        self.assertIn("not proof of joining",analytics["placement_explanation"])
        feed=self.client.get("/notifications",headers=self.accounts[0]["student_headers"]).json()
        self.assertGreaterEqual(feed["unread_count"],6)
        self.assertTrue(all(n["delivery"]=="simulated_in_app" for n in feed["notifications"]))

    def test_corrections_withdrawal_and_decline_remain_distinct(self):
        row=self.admin_change(self.rows[0],"offer_letter_status","issued")
        row=self.student_change(row,"submit_documents")
        row=self.admin_change(row,"verification_status","verified")
        row=self.admin_change(row,"documents_status","changes_requested")
        self.assertEqual(row["verification_status"],"pending")
        self.admin_change(row,"verification_status","verified",expected=409)
        row=self.student_change(row,"submit_documents")
        row=self.student_change(row,"decline")
        self.assertEqual(row["offer_letter_status"],"issued")
        self.assertEqual(row["documents_status"],"submitted")
        self.assertEqual(row["joining_status"],"pending")
        row2=self.admin_change(self.rows[1],"offer_letter_status","withdrawn",account=1)
        self.student_change(row2,"accept",account=1,expected=409)

    def test_ownership_roles_tenant_and_feed_recipient(self):
        a,b=self.accounts
        self.assertEqual(self.client.get("/admin/offers",headers=a["student_headers"]).status_code,403)
        self.assertEqual(self.client.get("/admin/offers",headers=a["recruiter_headers"]).status_code,403)
        self.assertEqual(self.client.get(f"/students/{b['support_student_id']}/offers",headers=a["student_headers"]).status_code,404)
        self.student_change(self.rows[1],"accept",expected=404)
        self.admin_change(self.rows[1],"offer_letter_status","issued",expected=404)
        own=self.client.get(f"/students/{a['support_student_id']}/offers",headers=a["student_headers"]).json()
        self.assertTrue(all(o["student_id"]==a["support_student_id"] for o in own["offers"]))
        student_feed=self.client.get("/notifications",headers=a["student_headers"]).json()
        notification=student_feed["notifications"][0]["id"]
        self.assertEqual(self.client.put(f"/notifications/{notification}/read",headers=a["headers"]).status_code,404)
        self.assertEqual(self.client.put(f"/notifications/{notification}/read",headers=b["student_headers"]).status_code,404)
        first=self.client.put(f"/notifications/{notification}/read",headers=a["student_headers"])
        self.assertEqual(first.status_code,200)
        second=self.client.put(f"/notifications/{notification}/read",headers=a["student_headers"])
        self.assertEqual(datetime.fromisoformat(first.json()["read_at"].replace("Z","+00:00")),datetime.fromisoformat(second.json()["read_at"].replace("Z","+00:00")))

    def test_stale_concurrent_and_duplicate_actions(self):
        row=self.admin_change(self.rows[0],"offer_letter_status","issued")
        account=self.accounts[0]
        def accept(_):
            return self.client.post(f"/students/{account['support_student_id']}/offers/{row['id']}/actions",
                headers=account["student_headers"],json=dict(action="accept",version=row["version"],reason="Concurrent synthetic acceptance"))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(accept,range(2)))
        self.assertEqual(sorted(r.status_code for r in results),[200,409])
        duplicate=self.client.post("/admin/offers",headers=account["headers"],
            json=dict(interview_id=row["interview_id"],reason="Retry duplicate offer creation"))
        self.assertEqual(duplicate.status_code,409)
        self.admin_change(row,"documents_status","changes_requested",expected=409)

    def test_selected_interview_required_and_candidate_options(self):
        a=self.accounts[0]
        calendar=self.client.get("/admin/schedules",headers=a["headers"]).json()
        not_selected=next(i for i in calendar["interviews"] if i["status"]=="scheduled")
        result=self.client.post("/admin/offers",headers=a["headers"],
            json=dict(interview_id=not_selected["id"],reason="Unselected interview must not create an offer"))
        self.assertEqual(result.status_code,409)
        options=self.client.get("/admin/offers/eligible-interviews",headers=a["headers"],params={"search":"Synthetic","limit":5}).json()
        self.assertLessEqual(len(options["candidates"]),5)
        self.assertNotIn(self.rows[0]["interview_id"],[c["interview_id"] for c in options["candidates"]])

    def test_rls_database_constraints_and_failed_action_atomicity(self):
        models=(Offer,OfferEvent,Notification)
        with tenant_session(2) as session:
            for model in models:
                records=session.scalars(select(model)).all()  # Omit filters intentionally to test RLS independently.
                self.assertTrue(records)
                self.assertTrue(all(r.college_id==2 for r in records))
        with SessionLocal() as session:
            for model in models:self.assertEqual(session.scalars(select(model)).all(),[])
        with engine.connect() as connection:
            policies=connection.execute(text("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname IN ('offers','offer_events','notifications')")).all()
            self.assertEqual(len(policies),3)
            self.assertTrue(all(all(row) for row in policies))
        for model in models:
            with self.subTest(table=model.__tablename__),self.assertRaises(DBAPIError):
                with tenant_session(1) as session:
                    row=session.scalar(select(model).where(model.college_id==1))
                    session.execute(update(model).where(model.college_id==1,model.id==row.id).values(college_id=2))
        with self.assertRaises(DBAPIError):
            with tenant_session(1) as session:
                session.execute(update(Offer).where(Offer.college_id==1,Offer.id==self.rows[0]["id"]).values(joining_status="joined"))
        with tenant_session(1) as session:
            row=session.scalar(select(Offer).where(Offer.college_id==1,Offer.id==self.rows[0]["id"]))
            self.assertEqual(row.joining_status,"pending")
            events=session.scalars(select(OfferEvent).where(OfferEvent.college_id==1,OfferEvent.offer_id==row.id)).all()
            self.assertEqual(len(events),1)

if __name__=="__main__":unittest.main()
