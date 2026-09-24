"""Read-only opportunities tested against PostgreSQL FORCE RLS, not fake data storage."""
import os
import unittest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from database import engine, tenant_session, SessionLocal
from main import app
from models import Job, Company, Student, Match
from engines.profile import collections
from engines.matching import calculate_match


class OpportunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("127.0.0.1", "localhost"):
            raise RuntimeError("Explicit localhost test database required.")
        cls.client = TestClient(app)
        cls.client.__enter__()
        cls.students = []
        for college in (1, 1, 2):
            response = cls.client.post('/auth/signup', json=dict(name='Synthetic navigation test',
                email=f'{uuid.uuid4().hex}@navigation.test', password='Synthetic-only-2026',college_id=college))
            assert response.status_code == 201, response.text
            value = response.json()
            cls.students.append((value['user']['student_id'], {'Authorization':'Bearer '+value['access_token']}))
        cls.sid, cls.headers = cls.students[0]
        cls.path = f'/students/{cls.sid}/opportunities'
        cls.profile = dict(name='Synthetic navigation test',branch='CSE',cgpa=8.5,backlog_count=0,
            aptitude_score=80,communication_score=80,interview_score=80,
            skills=[dict(skill_name='python',proficiency=80),dict(skill_name='sql',proficiency=70)],
            projects=[dict(title='Python SQL service',description='Synthetic integration example')],
            certifications=[dict(title='SQL course',description='Synthetic evidence')])
        assert cls.client.put(f'/students/{cls.sid}',headers=cls.headers,json=cls.profile).status_code == 200
        cls.jobs=[]
        for college in (1,2):
            response=cls.client.post('/auth/recruiter/signup',json=dict(email=f'{uuid.uuid4().hex}@navigation.test',
                password='Synthetic-only-2026',college_id=college,company=dict(name='Synthetic navigation company',industry='Testing')))
            assert response.status_code==201,response.text
            headers={'Authorization':'Bearer '+response.json()['access_token']}
            if college==1:cls.recruiter=headers
            for i in range(3 if college==1 else 1):
                response=cls.client.post('/recruiters/jobs',headers=headers,json=dict(title=f'Synthetic navigation role {i}',ctc=6,
                    min_cgpa=9.5 if i==2 else 6,eligible_branches=['CSE'],
                    required_skills=[dict(skill_name='python',min_proficiency=60),dict(skill_name='sql',min_proficiency=60)]))
                assert response.status_code==201,response.text
                cls.jobs.append(response.json())

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None,None,None)

    def test_actual_engine_parity_ranking_pagination_and_named_skill_gaps(self):
        response=self.client.get(self.path,headers=self.headers,params=dict(status='all',limit=20,target_job_id=self.jobs[0]['id']))
        self.assertEqual(response.status_code,200,response.text)
        data=response.json();target=data['target']
        with tenant_session(1) as session:
            student=session.scalar(select(Student).where(Student.id==self.sid,Student.college_id==1))
            job=session.scalar(select(Job).where(Job.id==self.jobs[0]['id'],Job.college_id==1))
            evidence=collections(session,student)
            expected=calculate_match(student,evidence['skills'],evidence['projects'],evidence['certifications'],job).model_dump()
        self.assertEqual({key:target[key] for key in expected},expected)
        self.assertAlmostEqual(sum(f['contribution'] for f in target['factor_breakdown']),target['match_score'])
        self.assertTrue(target['explanation'] and target['methodology'] and target['next_step'])
        self.assertEqual({g['skill_name'] for g in target['skill_gaps']},{'python','sql'})
        rows=data['items'];self.assertEqual(rows,sorted(rows,key=lambda r:(-r['match_score'],r['job_id'])))
        first=self.client.get(self.path,headers=self.headers,params=dict(status='all',limit=1)).json()
        second=self.client.get(self.path,headers=self.headers,params=dict(status='all',offset=1,limit=1)).json()
        self.assertEqual([first['items'][0]['job_id'],second['items'][0]['job_id']],[row['job_id'] for row in rows[:2]])
        eligible=self.client.get(self.path,headers=self.headers).json()
        self.assertTrue(all(row['eligible'] for row in eligible['items']))
        excluded=self.client.get(self.path,headers=self.headers,params=dict(status='excluded',target_job_id=self.jobs[2]['id'])).json()
        self.assertTrue(all(not row['eligible'] for row in excluded['items']))
        self.assertFalse(excluded['target']['eligible'])
        self.assertIn('no required skill gap was found',excluded['target']['explanation'])
        roles=[r['job_id'] for r in data['roles']]
        self.assertNotIn(self.jobs[-1]['id'],roles)
        tied=[r for r in roles if r in [self.jobs[0]['id'],self.jobs[1]['id']]]
        self.assertEqual(tied,sorted(tied))

    def test_access_controls_and_query_validation(self):
        self.assertEqual(self.client.get(self.path).status_code,401)
        self.assertEqual(self.client.get(self.path,headers=self.recruiter).status_code,403)
        for _,headers in self.students[1:]:
            self.assertEqual(self.client.get(self.path,headers=headers).status_code,404)
        self.assertEqual(self.client.get(self.path,headers=self.headers,params={'target_job_id':self.jobs[-1]['id']}).status_code,404)
        for params in ({'limit':21},{'offset':-1},{'status':'promoted'},{'target_job_id':0}):
            self.assertEqual(self.client.get(self.path,headers=self.headers,params=params).status_code,422)
        schema=self.client.get('/openapi.json').json()
        self.assertIn('/students/{student_id}/opportunities',schema['paths'])

    def test_missing_profile_evidence_is_explained_and_read_does_not_write_matches(self):
        empty={**self.profile,'cgpa':None,'skills':[],'projects':[],'certifications':[],
            'aptitude_score':None,'communication_score':None,'interview_score':None}
        self.client.put(f'/students/{self.sid}',headers=self.headers,json=empty)
        try:
            with tenant_session(1) as session:
                before=session.scalar(select(func.count(Match.id)).where(Match.college_id==1))
            response=self.client.get(self.path,headers=self.headers,params=dict(target_job_id=self.jobs[0]['id'])).json()
            self.assertEqual(response['eligible_count'],0)
            target=response['target'];self.assertEqual(target['match_score'],0)
            self.assertEqual(len(target['factor_breakdown']),5)
            self.assertTrue(all(f['missing'] for f in target['factor_breakdown']))
            self.assertTrue(all(g['status']=='critical' for g in target['skill_gaps']))
            self.assertTrue(target['missing_requirements'] and target['next_step'])
            with tenant_session(1) as session:
                self.assertEqual(before,session.scalar(select(func.count(Match.id)).where(Match.college_id==1)))
        finally:
            self.client.put(f'/students/{self.sid}',headers=self.headers,json=self.profile)

    def test_existing_recruiter_snapshots_unchanged_and_underlying_rls_fail_closed(self):
        with tenant_session(1) as session:
            before=[(row.id,row.match_score,row.override_action,row.explanation,row.calculated_at) for row in
                session.scalars(select(Match).where(Match.college_id==1).order_by(Match.id))]
        self.assertEqual(self.client.get(self.path,headers=self.headers).status_code,200)
        with tenant_session(1) as session:
            after=[(row.id,row.match_score,row.override_action,row.explanation,row.calculated_at) for row in
                session.scalars(select(Match).where(Match.college_id==1).order_by(Match.id))]
            self.assertEqual(before,after)
            # Deliberately omit application filters to test the second enforcement layer.
            self.assertTrue(all(row.college_id==1 for row in session.scalars(select(Job))))
            self.assertTrue(all(row.college_id==1 for row in session.scalars(select(Company))))
        with SessionLocal() as session:
            self.assertEqual(session.scalars(select(Job)).all(),[])
            self.assertEqual(session.scalars(select(Company)).all(),[])
