"""Assistant-authored synthetic sanity check against our own assumptions; NOT validated accuracy."""
import argparse
from collections import defaultdict
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import re
from sqlalchemy import select,func
from database import tenant_session
from models import User,Student,StudentSkill,Project,Certification,Job,Company,Interview,Offer
from schemas import ProfileUpdate
from engines.matching import calculate_match
from engines.readiness import calculate_readiness
from engines.risk import evaluate_support
from seed import DEMO_DRIVES,PHASE4_ROLES

LABEL="Assistant-authored synthetic sanity check against our own assumptions — not validated accuracy or independent human validation."
FIELDS=("name","branch","cgpa","backlog_count","aptitude_score","communication_score","interview_score")


def catalog(session,college):
    specs=[(i+1,j.title) for i,j in enumerate(DEMO_DRIVES)]+[(1,"Simulated Cloud Support Track")]+[
        (i+13,role[0]) for i,role in enumerate(PHASE4_ROLES)]
    result=[]
    for recruiter,title in specs:
        query=select(Job).join(Company,Company.id==Job.company_id).join(User,User.id==Company.recruiter_user_id).where(
            Job.college_id==college,Company.college_id==college,User.college_id==college,
            User.email==f"recruiter{recruiter:02d}@demo.jobjugaad.test",Job.title==title)
        result.append(session.scalars(query).one())
    return result


def dataset_summary(session,college):
    population=session.execute(select(User.email,Student.id,Student.cgpa).join(Student,Student.user_id==User.id)
        .where(User.college_id==college,Student.college_id==college)).all()
    population=[r for r in population if re.fullmatch(r"(student[0-9]+|support[0-9]+)@demo\.jobjugaad\.test",r.email)]
    ids={r.id for r in population}
    accepted=set(session.scalars(select(Offer.student_id).where(Offer.college_id==college,Offer.student_id.in_(ids),
        Offer.is_synthetic.is_(True),Offer.offer_letter_status=="issued",Offer.acceptance_status=="accepted",Offer.joining_status!="not_joined")))
    joined=set(session.scalars(select(Offer.student_id).where(Offer.college_id==college,Offer.student_id.in_(ids),
        Offer.is_synthetic.is_(True),Offer.joining_status=="joined")))
    selected=set(session.scalars(select(Interview.student_id).where(Interview.college_id==college,Interview.student_id.in_(ids),
        Interview.seed_key.startswith("phase4:"),Interview.status=="selected")))
    companies=session.scalars(select(User.email).join(Company,Company.recruiter_user_id==User.id)
        .where(User.college_id==college,Company.college_id==college)).all()
    bins=defaultdict(lambda:dict(students=0,selected=0,accepted=0,joined=0))
    for row in population:
        group="CGPA below 6" if row.cgpa is not None and row.cgpa<6 else "CGPA 6 to below 8" if row.cgpa is not None and row.cgpa<8 else "CGPA 8 or above" if row.cgpa is not None else "CGPA unknown"
        bins[group]["students"]+=1
        for key,values in (("selected",selected),("accepted",accepted),("joined",joined)):
            bins[group][key]+=int(row.id in values)
    return dict(synthetic_students=len(population),synthetic_companies=sum(bool(re.fullmatch(r"recruiter[0-9]+@demo\.jobjugaad\.test",email)) for email in companies),
        cgpa_groups=dict(sorted(bins.items())),explanation="Outcomes are fictional imports from proposed correlated generation assumptions, not observed placements. Earlier 300 profiles and four support examples are preserved; new profiles share a noisy preparation factor. Selected, active accepted and joined are distinct counts.")


def evaluate(college=1):
    expected=json.loads(Path(__file__).with_name("evaluation_expected.json").read_text(encoding="utf-8"))
    now=datetime.now(timezone.utc)
    cases=[]
    with tenant_session(college) as session:
        jobs=catalog(session,college)
        support_job=next(job for job in jobs if job.title==expected["support_role"])
        for label in expected["samples"]:
            student=session.scalars(select(Student).join(User,User.id==Student.user_id).where(
                Student.college_id==college,User.college_id==college,
                User.email==f"student{label['seed_index']:02d}@demo.jobjugaad.test")).one()
            skills=session.scalars(select(StudentSkill).where(StudentSkill.college_id==college,StudentSkill.student_id==student.id).order_by(StudentSkill.id)).all()
            projects=session.scalars(select(Project).where(Project.college_id==college,Project.student_id==student.id).order_by(Project.id)).all()
            certs=session.scalars(select(Certification).where(Certification.college_id==college,Certification.student_id==student.id).order_by(Certification.id)).all()
            activity=session.scalar(select(func.count()).select_from(Interview).where(Interview.college_id==college,Interview.student_id==student.id,
                Interview.status.in_(["completed","selected","rejected"]),Interview.end_time>=now-timedelta(days=30),Interview.end_time<=now))
            profile=ProfileUpdate(**{name:getattr(student,name) for name in FIELDS},
                skills=[dict(skill_name=s.skill_name,proficiency=s.proficiency) for s in skills],
                projects=[dict(title=p.title,description=p.description) for p in projects],
                certifications=[dict(title=c.title,description=c.description) for c in certs])
            inputs=dict(profile=profile.model_dump(mode="json"),completed_interviews=activity)
            digest=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()
            if digest!=label["input_sha256"]:
                raise RuntimeError(f"Frozen inputs changed for sample {label['seed_index']}; inspect drift instead of relabeling.")
            calculations=[dict(job_title=job.title,catalog_order=i,**calculate_match(student,skills,projects,certs,job).model_dump(mode="json")) for i,job in enumerate(jobs)]
            ranked=sorted((r for r in calculations if r["eligible"]),key=lambda r:(-r["match_score"],r["catalog_order"]))[:3]
            actual=[row["job_title"] for row in ranked]
            readiness=calculate_readiness(student,skills,projects).model_dump(mode="json")
            support=evaluate_support(student,skills,support_job,activity).model_dump(mode="json")
            wanted=label["expected_top3"]
            cases.append(dict(seed_index=label["seed_index"],inputs=inputs,input_sha256=digest,review_reason=label["review_reason"],
                expected_top3=wanted,actual_top3=actual,hits=len(set(wanted)&set(actual)),
                missed=[title for title in wanted if title not in actual],unexpected=[title for title in actual if title not in wanted],
                matching_evidence=calculations,expected_readiness_band=label["expected_readiness_band"],readiness=readiness,
                readiness_agrees=readiness["band"]==label["expected_readiness_band"],expected_support_flag=label["expected_support_flag"],
                support=support,support_agrees=support["flagged"]==label["expected_support_flag"]))
        dataset=dataset_summary(session,college)
    hits=sum(row["hits"] for row in cases);returned=sum(len(row["actual_top3"]) for row in cases)
    return dict(label=LABEL,evaluated_at=now.isoformat(),support_role=expected["support_role"],dataset=dataset,
        matching=dict(expected_slots=30,returned_slots=returned,hits=hits,precision_fraction=f"{hits}/{returned}" if returned else "undefined (no returned matches)",recall_fraction=f"{hits}/30"),
        face_validity=dict(profiles=10,readiness_agreements=sum(c["readiness_agrees"] for c in cases),support_agreements=sum(c["support_agrees"] for c in cases)),
        limitations=["No real data or independent human rater.","Convenience sample of ten profiles; no expected Not Ready example.",
            "Expected roles reflect specialization and appropriate level; the weighted engine measures requirement coverage and may favor easier roles.",
            "Correlations and outcomes are deliberately generated, not learned or validated.","No weights, thresholds, labels or inputs were tuned to the observed result."],cases=cases)


def markdown(result):
    match=result["matching"];face=result["face_validity"]
    lines=["# Phase 4 synthetic evaluation","",f"**{LABEL}**","",f"Observed at {result['evaluated_at']}. Frozen expectations: commit c2748bf, backend/evaluation_expected.json.",
        "",f"Matching reproduced **{match['hits']} of 30 expected matches** across ten profiles. The engine returned {match['returned_slots']} eligible slots. Synthetic micro precision: {match['precision_fraction']}; recall: {match['recall_fraction']}. These are self-labeled sanity-check fractions, not real-world accuracy.",
        "",f"Face-validity review agreed on **{face['readiness_agreements']} of 10 readiness bands** and **{face['support_agreements']} of 10 support flags**. The same ten profiles were used for both reviews.",
        "","## Per-profile matching comparison","", "| Seed | Expected top three | Actual top three | Reproduced |","|---|---|---|---|"]
    for case in result["cases"]:
        lines.append(f"| {case['seed_index']} | {'; '.join(case['expected_top3'])} | {'; '.join(case['actual_top3']) or 'No eligible matches'} | {case['hits']}/3 |")
    lines+=["","## Mismatches and observations",""]
    for case in result["cases"]:
        if case["missed"]:
            lines.append(f"- Seed {case['seed_index']}: missed {'; '.join(case['missed'])}. Returned instead: {'; '.join(case['unexpected']) or 'fewer eligible slots'}.")
            for title in case["missed"]:
                evidence=next(r for r in case["matching_evidence"] if r["job_title"]==title)
                lines.append("  - "+title+": "+("Eligible, but outranked under the current requirement-coverage weights." if evidence["eligible"] else "Excluded: "+"; ".join(evidence["missing_requirements"])))
    if all(not case["missed"] for case in result["cases"]):lines.append("No top-three set mismatches in this small self-labeled sample.")
    lines+=["","The reviewer favored role specialization and appropriate level. The formula rewards meeting listed targets and exact project keywords; lower-target apprentice roles can therefore outrank specialist roles. Equal scores use the frozen catalog order. These are inspectable limitations, not reasons to silently alter the expected labels or tune the result.","",
        "## Readiness and support face-validity review","", "| Seed | Expected readiness | Actual readiness | Expected support flag | Actual flag | Review result |","|---|---|---|---|---|---|"]
    for case in result["cases"]:
        agreements="Agrees" if case["readiness_agrees"] and case["support_agrees"] else "MISMATCH — inspect factors below"
        lines.append(f"| {case['seed_index']} | {case['expected_readiness_band']} | {case['readiness']['band']} | {case['expected_support_flag']} | {case['support']['flagged']} | {agreements} |")
    for case in result["cases"]:
        ready=case["readiness"];support=case["support"]
        lines+=["",f"### Seed {case['seed_index']}","",f"Pre-run judgment: {case['review_reason']}","",
            f"Readiness: **{ready['score']}/100, {ready['band']}**. {ready['explanation']}","",
            "| Factor | Normalized input | Weight | Contribution | Evidence |","|---|---|---|---|---|"]
        for factor in ready["breakdown"]:lines.append(f"| {factor['label']} | {factor['value']} | {factor['weight']} | {factor['contribution']} | {factor['evidence']} |")
        lines+=["",f"Support: **{support['score']}/3 indicators**, flag **{support['flagged']}** for {result['support_role']}. {support['explanation']}","",
            "| Factor | Observed input | Threshold | Contribution | Evidence |","|---|---|---|---|---|"]
        for factor in support["contributing_factors"]:lines.append(f"| {factor['label']} | {factor['value']} | {factor['threshold']} | {factor['contribution']} | {factor['explanation']} |")
        for intervention in support["recommendation"]:lines.append(f"- {intervention['category']}: {intervention['action']}")
        if not case["readiness_agrees"]:lines.append("Readiness mismatch: the qualitative expectation differs from the fixed weighted contributions shown above; the expectation and formula are unchanged.")
        if not case["support_agrees"]:lines.append("Support mismatch: inspect the observed skill gaps, known interview score and completed-record count above; the expectation and rule are unchanged.")
    data=result["dataset"]
    lines+=["","## Dataset check","",f"Observed synthetic population: **{data['synthetic_students']} students and {data['synthetic_companies']} companies**. {data['explanation']}","",
        "| CGPA group | Students | Selected | Active accepted offers (students) | Joined |","|---|---|---|---|---|"]
    for label,group in data["cgpa_groups"].items():lines.append(f"| {label} | {group['students']} | {group['selected']} | {group['accepted']} | {group['joined']} |")
    lines+=["","Counts come from the actual seeded records. Compare each outcome count with its group's student count; this describes a deliberately generated association, not a real placement forecast.","","## Limits",""]
    lines += ["- "+limit for limit in result["limitations"]]
    lines+=["","Full matching scores, factors, missing requirements and fixed explanations for every evaluated profile/role are retained in phase4-results.json. No bare score is used as an evaluation conclusion.",""]
    return "\n".join(lines)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--college",type=int,default=1)
    parser.add_argument("--output-dir",type=Path,default=Path(__file__).resolve().parent.parent/"evaluations")
    arguments=parser.parse_args()
    result=evaluate(arguments.college)
    arguments.output_dir.mkdir(parents=True,exist_ok=True)
    (arguments.output_dir/"phase4-results.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    (arguments.output_dir/"phase4-report.md").write_text(markdown(result),encoding="utf-8")
    print(json.dumps({key:result[key] for key in ("label","matching","face_validity","dataset")},indent=2))
