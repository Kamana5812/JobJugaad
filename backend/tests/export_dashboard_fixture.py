"""Export only local synthetic fixtures for React rendering checks."""
import os
import json
from pathlib import Path
from types import SimpleNamespace
from sqlalchemy import select
from database import tenant_session, engine
from models import Student, Job
from engines.profile import profile_response
from engines.opportunities import student_opportunities
from engines.analytics import overview
from engines.scheduling import calendar_board
from engines.support import report
from engines.talent import match_results
if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("127.0.0.1", "localhost"):
    raise RuntimeError("Explicit localhost test database required; never export production profiles.")
Path(".local").mkdir(exist_ok=True)
with tenant_session(1) as session:
    student=session.scalar(select(Student).where(Student.college_id==1,Student.name=='Synthetic Student 301').order_by(Student.id))
    assert student is not None
    user=SimpleNamespace(college_id=1)
    job=session.scalar(select(Job).where(Job.college_id==1,Job.title=='Simulated Python Backend Engineer').order_by(Job.id))
    support_job=session.scalar(select(Job).where(Job.college_id==1,Job.title=='Simulated Cloud Support Track').order_by(Job.id))
    payload=dict(profile=profile_response(session,student).model_dump(mode='json'),
        opportunities=student_opportunities(session,student,'all',0,3,job.id).model_dump(mode='json'),
        analytics=overview(session,user).model_dump(mode='json'),board=calendar_board(session,user).model_dump(mode='json'),
        support=report(session,user,support_job.id).model_dump(mode='json'),
        candidates=match_results(session,job,'all',0,3).model_dump(mode='json')['candidates'])
    Path('.local/dashboard-render-data.json').write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
print('Saved ignored rendering inputs from actual local synthetic records; no passwords or tokens exported.')
