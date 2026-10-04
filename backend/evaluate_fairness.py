"""Synthetic subgroup/counterfactual audit of existing weighted rules, never a fairness certification."""
import argparse
import json
import os
import re
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from sqlalchemy import select
from database import engine,tenant_session
from models import User,Student,StudentSkill,Project,Certification
from engines.matching import calculate_match
from seed import DEMO_DRIVES

LABEL='Synthetic rule-behavior audit; not independently validated fairness or accuracy.'
def band(cgpa): return 'missing' if cgpa is None else 'below 6.5' if cgpa<6.5 else '6.5 to below 8' if cgpa<8 else '8 and above'

def summarize(rows):
    count=len(rows);eligible=sum(r['eligible'] for r in rows);hard=sum(bool(r['hard_cgpa']) for r in rows)
    strong=[r for r in rows if r['strong_evidence']]
    return {'count':count,'eligible':eligible,'eligible_rate':round(eligible/count*100,2) if count else None,
        'mean_match_score':round(sum(r['score'] for r in rows)/count,2) if count else None,
        'cgpa_exclusions':hard,'strong_skill_project_count':len(strong),'strong_skill_project_excluded':sum(not r['eligible'] for r in strong),
        'top20_count':sum(r['top20'] for r in rows),'small_group':count<30,
        'explanation':f'{eligible} of {count} synthetic profiles meet the current hard rules and score threshold; {hard} fail the CGPA floor. Strong evidence means skill factor >=80 and project factor >=50. This is descriptive rule behavior, not proof of fairness.'}

def counterfactuals(jobs):
    cases=[]
    for job in jobs:
        for proficiency in (40,65,85,100):
            skills=[SimpleNamespace(skill_name=r['skill_name'],proficiency=proficiency) for r in job.required_skills]
            projects=[SimpleNamespace(title='Controlled coursework',description=' '.join(s.skill_name for s in skills))]
            fixed={'branch':job.eligible_branches[0],'backlog_count':0,'aptitude_score':80,'communication_score':80,'interview_score':80}
            outputs=[calculate_match(SimpleNamespace(cgpa=cgpa,**fixed),skills,projects,[],job).model_dump(mode='json') for cgpa in (5.5,9.0)]
            cases.append({'drive':job.title,'changed_input':'CGPA only: 5.5 versus 9.0','skill_proficiency':proficiency,
                'lower_cgpa':outputs[0],'higher_cgpa':outputs[1],'score_difference':round(outputs[1]['match_score']-outputs[0]['match_score'],2),
                'eligibility_changed':outputs[0]['eligible']!=outputs[1]['eligible'],
                'interpretation':'Hard CGPA floors can exclude a skilled lower-CGPA candidate before ranking. The academic factor also changes the score when every other input is identical. Human overrides remain auditable exceptions, not evidence that this effect is fair.'})
    return cases

def evaluate(college=1):
    if os.environ.get('ALLOW_TEST_DATABASE')!='yes' or engine.url.host not in ('127.0.0.1','localhost'):
        raise RuntimeError('Evaluation requires an explicitly authorized local synthetic dataset.')
    jobs=[SimpleNamespace(**j.model_dump()) for j in DEMO_DRIVES]
    with tenant_session(college) as session:
        students=session.execute(select(Student,User.email).join(User,User.id==Student.user_id).where(
            Student.college_id==college,User.college_id==college,User.email.like('student%@demo.jobjugaad.test'))).all()
        students=[s for s,email in students if re.fullmatch(r'student[0-9]+@demo\.jobjugaad\.test',email)]
        ids=[s.id for s in students]
        skills=defaultdict(list);projects=defaultdict(list);certs=defaultdict(list)
        for model,target in ((StudentSkill,skills),(Project,projects),(Certification,certs)):
            for row in session.scalars(select(model).where(model.college_id==college,model.student_id.in_(ids))).all(): target[row.student_id].append(row)
        reports=[]
        for job in jobs:
            rows=[]
            for student in students:
                result=calculate_match(student,skills[student.id],projects[student.id],certs[student.id],job)
                factors={f.key:f.value for f in result.factor_breakdown}
                rows.append({'id':student.id,'branch':student.branch,'cgpa_band':band(student.cgpa),'score':result.match_score,
                    'eligible':result.eligible,'hard_cgpa':student.cgpa is None or student.cgpa<job.min_cgpa,
                    'strong_evidence':factors['skills']>=80 and factors['projects']>=50,'top20':False})
            top={r['id'] for r in sorted((r for r in rows if r['eligible']),key=lambda r:(-r['score'],r['id']))[:20]}
            for row in rows: row['top20']=row['id'] in top
            groups={}
            for kind in ('cgpa_band','branch'):
                buckets=defaultdict(list)
                for row in rows: buckets[row[kind]].append(row)
                groups[kind]={key:summarize(value) for key,value in sorted(buckets.items())}
            reports.append({'drive':job.title,'min_cgpa':job.min_cgpa,'weights':job.weights,'groups':groups,'total':summarize(rows)})
    return {'label':LABEL,'evaluated_at':datetime.now(timezone.utc).isoformat(),'synthetic_profile_count':len(students),'drives':reports,
        'counterfactuals':counterfactuals(jobs),'limitations':['Synthetic correlated data and unvalidated starting weights do not establish real-world fairness.','No gender, caste, disability or socioeconomic labels are collected here; no protected-group parity claim is possible.','CGPA and branch eligibility restrictions are recruiter policies. Scores and top-20 rates are not calibrated outcome probabilities.','Missing groups and samples below 30 must not be interpreted as reliable population comparisons.'],
        'recommended_actions':['Review CGPA floors with recruiters when strong skills/projects are excluded.','Inspect named factors and missing evidence; record any human exception with a reason.','Collect consented, representative real outcomes before drawing subgroup fairness conclusions.','Do not change weights or thresholds automatically based on this synthetic audit.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--college',type=int,default=1);args=parser.parse_args()
    result=evaluate(args.college);Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'profiles':result['synthetic_profile_count'],'drives':len(result['drives']),'counterfactual_pairs':len(result['counterfactuals']),'label':LABEL}))
