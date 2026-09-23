"""Idempotent synthetic Phase 2 demonstration; not real accuracy data."""
import random
import secrets
from sqlalchemy import select, text
from auth import hash_password
from database import tenant_session, initialize_schema
from models import User, Student
from schemas import ProfileUpdate, SkillInput, EvidenceInput, JobInput
from engines.profile import save_profile

# These are simulated requirements, not statements about real employers.
DEMO_DRIVES = [
    JobInput(title="Simulated Python Backend Engineer", ctc=6, min_cgpa=6, max_backlogs=1,
        eligible_branches=["CSE", "ECE"], required_skills=[dict(skill_name="python", min_proficiency=60), dict(skill_name="sql", min_proficiency=50)]),
    JobInput(title="Simulated React Frontend Engineer", ctc=5.5, min_cgpa=6.5, max_backlogs=0,
        eligible_branches=["CSE", "ECE", "EE"], required_skills=[dict(skill_name="react", min_proficiency=65), dict(skill_name="git", min_proficiency=50)]),
    JobInput(title="Simulated Java Graduate Engineer", ctc=4.5, min_cgpa=5.5, max_backlogs=2,
        eligible_branches=["CSE", "ECE", "ME", "EE"], required_skills=[dict(skill_name="java", min_proficiency=55), dict(skill_name="communication", min_proficiency=50)]),
]

def seed_students(count=300, college_id=1):
    rng = random.Random(2026)
    created = 0
    # Unshared random passwords prevent public login to the synthetic seed accounts.
    unused_hash = hash_password(secrets.token_urlsafe(32))
    with tenant_session(college_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(20260102)"))
        for index in range(1, count + 1):
            email = f"student{index:02d}@demo.jobjugaad.test"
            level = rng.randint(15, 95)
            skills = [SkillInput(skill_name=skill, proficiency=max(0, min(100, level + rng.randint(-15, 15))))
                for skill in rng.sample(["python", "sql", "react", "java", "communication", "git"], 3)]
            projects = [EvidenceInput(title=f"Synthetic project {p + 1}", description="Synthetic coursework example for testing; not a real student achievement.")
                for p in range(rng.randint(0, 5))]
            payload = ProfileUpdate(name=f"Synthetic Student {index:02d}", branch=rng.choice(["CSE", "ECE", "ME", "EE"]),
                cgpa=round(rng.uniform(4, 10), 2), backlog_count=rng.randint(0, 3), skills=skills, projects=projects,
                aptitude_score=level, communication_score=rng.randint(20, 95), interview_score=rng.randint(10, 95),
                certifications=[EvidenceInput(title="Synthetic course completion", description="Demo certificate; not an accredited credential.")] if index % 2 else [])
            if index > 50:
                for project in payload.projects:
                    project.description = "Synthetic coursework using " + ", ".join(s.skill_name for s in skills) + "; demonstration only."
            existing = session.scalar(select(User.id).where(User.email == email, User.college_id == college_id))
            if existing:
                continue
            user = User(email=email, password_hash=unused_hash, college_id=college_id, role="student")
            session.add(user)
            session.flush()
            student = Student(user_id=user.id, college_id=college_id, name=payload.name,
                resume_text=f"Synthetic resume for Student {index:02d}. For testing only.")
            session.add(student)
            session.flush()
            save_profile(session, student, payload)
            created += 1
    return created


def seed_companies(college_id=1):
    from models import Company, Job, Match
    from engines.talent import run_matching
    unused_hash = hash_password(secrets.token_urlsafe(32))
    created = 0
    demonstrations = []
    with tenant_session(college_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(20260103)"))
        for index in range(1, 13):
            email = f"recruiter{index:02d}@demo.jobjugaad.test"
            user = session.scalar(select(User).where(User.email == email, User.college_id == college_id))
            if user is None:
                user = User(email=email, password_hash=unused_hash, role="recruiter", college_id=college_id)
                session.add(user)
                session.flush()
                session.add(Company(college_id=college_id, recruiter_user_id=user.id,
                    name=f"Synthetic Company {index:02d}", industry="Simulated technology services"))
                session.flush()
                created += 1
            company = session.scalar(select(Company).where(Company.college_id == college_id, Company.recruiter_user_id == user.id))
            if index <= len(DEMO_DRIVES):
                payload = DEMO_DRIVES[index - 1]
                job = session.scalar(select(Job).where(Job.college_id == college_id, Job.company_id == company.id, Job.title == payload.title).with_for_update())
                if job is None:
                    job = Job(college_id=college_id, company_id=company.id, **payload.model_dump())
                    session.add(job)
                    session.flush()
                if session.scalar(select(Match.id).where(Match.college_id == college_id, Match.job_id == job.id).limit(1)) is None:
                    demonstrations.append(run_matching(session, job).model_dump())
    return created, demonstrations



def seed_phase3(college_id=1):
    from datetime import datetime, timedelta, timezone
    from models import Company, Job, Interview, RiskPrediction
    from engines.scheduling import lock_calendar
    from engines.support import run_support
    created = {"support_students":0, "interviews":0}
    unused_hash = hash_password(secrets.token_urlsafe(32))
    with tenant_session(college_id) as session:
        lock_calendar(session, college_id)
        recruiter = session.scalar(select(User).where(User.college_id == college_id, User.email == "recruiter01@demo.jobjugaad.test"))
        company = session.scalar(select(Company).where(Company.college_id == college_id, Company.recruiter_user_id == recruiter.id))
        job = session.scalar(select(Job).where(Job.college_id == college_id, Job.company_id == company.id, Job.title == "Simulated Cloud Support Track"))
        if job is None:
            payload = JobInput(title="Simulated Cloud Support Track", ctc=5, min_cgpa=5, max_backlogs=3,
                eligible_branches=["CSE","ECE","EE","ME"],
                required_skills=[dict(skill_name=name,min_proficiency=60) for name in ("python","sql","aws","git")])
            job = Job(college_id=college_id, company_id=company.id, **payload.model_dump())
            session.add(job); session.flush()
        support_students = []
        for index in range(1,5):
            email = f"support{index:02d}@demo.jobjugaad.test"
            user = session.scalar(select(User).where(User.college_id == college_id, User.email == email))
            if user is None:
                user = User(college_id=college_id,email=email,password_hash=unused_hash,role="student")
                session.add(user);session.flush()
                student = Student(college_id=college_id,user_id=user.id,name=f"Synthetic Support Student {index:02d}")
                session.add(student);session.flush()
                save_profile(session,student,ProfileUpdate(name=student.name,branch="CSE",cgpa=6.2,
                    skills=[SkillInput(skill_name="python",proficiency=20+index)],projects=[],
                    aptitude_score=35,communication_score=40,interview_score=15+index*5))
                created["support_students"] += 1
            else:
                student = session.scalar(select(Student).where(Student.college_id == college_id,Student.user_id == user.id))
            support_students.append(student)
        now = datetime.now(timezone.utc)
        anchor = (now+timedelta(days=1)).replace(hour=4,minute=30,second=0,microsecond=0)
        student = support_students[0]  # Never attach demonstration bookings to a real account.
        demo_jobs = session.scalars(select(Job).where(Job.college_id == college_id,Job.title.in_([d.title for d in DEMO_DRIVES])).order_by(Job.id).limit(2)).all()
        fixtures = [
            ("phase3-double-booking-a",student.id,demo_jobs[0].id,anchor,"scheduled","demo hall","demo panel"),
            ("phase3-double-booking-b",student.id,demo_jobs[1].id,anchor+timedelta(minutes=15),"scheduled","demo hall","demo panel"),
            ("phase3-participation-a",support_students[3].id,job.id,now-timedelta(days=3),"completed","practice room a","mentor a"),
            ("phase3-participation-b",support_students[3].id,job.id,now-timedelta(days=6),"completed","practice room b","mentor b"),
        ]
        for key, student_id, job_id, start, status, venue, panel in fixtures:
            if session.scalar(select(Interview.id).where(Interview.college_id == college_id,Interview.seed_key == key)) is None:
                # Deliberately imported conflict fixture. Normal API confirmations cannot create conflicts.
                session.add(Interview(college_id=college_id,student_id=student_id,job_id=job_id,scheduled_time=start,
                    end_time=start+timedelta(minutes=30),status=status,venue=venue,panel_id=panel,seed_key=key))
                created["interviews"] += 1
        session.flush()
        if session.scalar(select(RiskPrediction.id).where(RiskPrediction.college_id == college_id,RiskPrediction.job_id == job.id).limit(1)) is None:
            report = run_support(session,recruiter,job.id)
            created["flagged_for_review"] = report.flagged_count
        created["support_job_id"] = job.id
    return created



# Phase 4 population: proposed synthetic distributions, NOT observed placement statistics.
# Shared preparation influences CGPA/skills/assessments; independent noise leaves realistic exceptions.
PHASE4_ROLES = [
    ("Simulated Python Cloud Engineer", 9, 7, 60, [("python",75),("sql",65),("aws",60)]),
    ("Simulated Data Engineering Associate", 7, 6.5, 60, [("python",65),("sql",70),("git",55)]),
    ("Simulated Backend Apprentice", 3.5, 4, 45, [("python",35),("git",30)]),
    ("Simulated React Product Engineer", 9, 7, 60, [("react",75),("javascript",70),("css",60)]),
    ("Simulated Web UI Developer", 6.5, 6, 60, [("react",60),("css",55),("git",50)]),
    ("Simulated Web Apprentice", 3.5, 4, 45, [("javascript",30),("git",25)]),
    ("Simulated Java Platform Engineer", 8, 7, 60, [("java",75),("sql",65),("git",60)]),
    ("Simulated Quality Automation Associate", 5, 5.5, 55, [("python",50),("java",50),("git",50)]),
    ("Simulated General Support Trainee", 3, 4, 45, [("communication",30),("git",25)]),
]


def phase4_profile(index):
    rng=random.Random(20260400+index)
    preparation=rng.betavariate(2.4,2.0)
    bounded=lambda value,low=0,high=100: round(max(low,min(high,value)),2)
    cgpa=bounded(4.2+5.5*preparation+rng.gauss(0,0.5),4,9.95)
    tracks=(("python","sql","git","aws"),("react","javascript","css","git"),("java","sql","git","communication"))
    track=tracks[index%3]
    skill_names=list(dict.fromkeys((*track,"communication")))
    skills=[SkillInput(skill_name=name,proficiency=bounded(18+80*preparation+rng.gauss(0,12),10,99)) for name in skill_names]
    projects=[EvidenceInput(title=f"Synthetic {track[0]} project {n+1}",
        description="Synthetic coursework using "+", ".join(rng.sample(list(track),rng.randint(1,len(track))))+"; demonstration, not verified achievement.")
        for n in range(max(0,min(5,round(5*preparation+rng.gauss(0,0.8)))))]
    aptitude=bounded(15+80*preparation+rng.gauss(0,11),5,99)
    communication=bounded(20+70*preparation+rng.gauss(0,15),5,99)
    interview=None if index%17==0 else bounded(12+85*preparation+rng.gauss(0,14),5,99)
    backlogs=0 if preparation>0.55 or rng.random()<preparation else rng.randint(1,3)
    certs=[EvidenceInput(title=f"Synthetic {track[0]} course {n+1}",description="Simulated completion; no accreditation claimed.")
        for n in range(max(0,min(4,round(3*preparation+rng.gauss(0,0.6)))))]
    profile=ProfileUpdate(name=f"Synthetic Student {index:02d}",
        branch=rng.choices(["CSE","ECE","EE","ME"],weights=[45,25,15,15])[0],
        cgpa=cgpa,backlog_count=backlogs,skills=skills,projects=projects,certifications=certs,
        aptitude_score=aptitude,communication_score=communication,interview_score=interview)
    # These are data-generation probabilities, not model outputs, accuracy or individual forecasts.
    selected=rng.random()<min(0.92,0.08+0.72*preparation+0.12*(cgpa-4)/6)
    activity=max(0,min(3,round(3*preparation+rng.gauss(0,0.7))))
    outcome_roll=rng.random()
    return profile,dict(track=index%3,selected=selected,activity=activity,outcome_roll=outcome_roll)


def seed_phase4_students(college_id=1):
    from sqlalchemy import insert
    from models import StudentSkill, Project, Certification
    from engines.readiness import calculate_readiness
    unused_hash=hash_password(secrets.token_urlsafe(32))
    created=0
    with tenant_session(college_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(20260402, :college)"),{"college":college_id})
        existing=set(session.scalars(select(User.email).where(User.college_id==college_id)))
        # 4,796 numbered profiles + the four preserved Phase 3 support profiles = 4,800 synthetic profiles.
        missing=[i for i in range(301,4797) if f"student{i:02d}@demo.jobjugaad.test" not in existing]
        for offset in range(0,len(missing),200):
            indices=missing[offset:offset+200]
            profiles={i:phase4_profile(i)[0] for i in indices}
            users=session.execute(insert(User).returning(User.id,User.email),[
                dict(college_id=college_id,email=f"student{i:02d}@demo.jobjugaad.test",role="student",password_hash=unused_hash) for i in indices]).all()
            user_ids={u.email:u.id for u in users}
            student_values=[]
            for i,p in profiles.items():
                data=p.model_dump(exclude={"skills","projects","certifications"})
                data["readiness_score"]=calculate_readiness(p,p.skills,p.projects).score
                student_values.append(dict(college_id=college_id,user_id=user_ids[f"student{i:02d}@demo.jobjugaad.test"],
                    resume_text=f"Phase 4 synthetic resume {i}; demonstration only.",**data))
            students=session.execute(insert(Student).returning(Student.id,Student.user_id),student_values).all()
            student_ids={s.user_id:s.id for s in students}
            for model,key in ((StudentSkill,"skills"),(Project,"projects"),(Certification,"certifications")):
                values=[dict(college_id=college_id,student_id=student_ids[user_ids[f"student{i:02d}@demo.jobjugaad.test"]],**item.model_dump())
                    for i,p in profiles.items() for item in getattr(p,key)]
                if values:session.execute(insert(model),values)
            created+=len(indices)
    return created


def seed_phase4_catalog(college_id=1):
    from models import Company,Job
    unused_hash=hash_password(secrets.token_urlsafe(32))
    created=0
    with tenant_session(college_id) as session:
        session.execute(text("SELECT pg_advisory_xact_lock(20260403, :college)"),{"college":college_id})
        for index in range(13,46):
            email=f"recruiter{index:02d}@demo.jobjugaad.test"
            user=session.scalar(select(User).where(User.college_id==college_id,User.email==email))
            if user is None:
                user=User(college_id=college_id,email=email,password_hash=unused_hash,role="recruiter")
                session.add(user);session.flush()
                session.add(Company(college_id=college_id,recruiter_user_id=user.id,
                    name=f"Synthetic Company {index:02d}",industry="Simulated technology services"))
                session.flush();created+=1
            company=session.scalar(select(Company).where(Company.college_id==college_id,Company.recruiter_user_id==user.id))
            if index<22:
                title,ctc,cgpa,threshold,skills=PHASE4_ROLES[index-13]
                job=session.scalar(select(Job).where(Job.college_id==college_id,Job.company_id==company.id,Job.title==title))
                if job is None:
                    payload=JobInput(title=title,ctc=ctc,min_cgpa=cgpa,min_match_score=threshold,
                        max_backlogs=3 if threshold==45 else 1,eligible_branches=["CSE","ECE","EE","ME"],
                        required_skills=[dict(skill_name=skill,min_proficiency=target) for skill,target in skills])
                    session.add(Job(college_id=college_id,company_id=company.id,**payload.model_dump()))
    return created


def seed_phase4_outcomes(college_id=1):
    from datetime import datetime,timedelta,timezone
    from sqlalchemy import insert
    from models import Job,Interview,Offer,OfferEvent,Notification,Company
    from engines.scheduling import lock_calendar
    created=dict(interviews=0,offers=0)
    with tenant_session(college_id) as session:
        lock_calendar(session,college_id)
        session.execute(text("SELECT pg_advisory_xact_lock(20260401, :college)"),{"college":college_id})
        jobs={j.title:j for j in session.scalars(select(Job).join(Company,Company.id==Job.company_id).join(User,User.id==Company.recruiter_user_id).where(
            Job.college_id==college_id,Company.college_id==college_id,User.college_id==college_id,
            User.email.in_([f"recruiter{i:02d}@demo.jobjugaad.test" for i in range(13,22)])))}
        titles=("Simulated Backend Apprentice","Simulated Web Apprentice","Simulated General Support Trainee")
        anchor=min(jobs[title].created_at for title in titles)
        student_rows=session.execute(select(User.email,Student.id,Student.user_id,Student.resume_text)
            .join(Student,Student.user_id==User.id).where(User.college_id==college_id,Student.college_id==college_id)).all()
        students={row.email:row for row in student_rows}
        existing_interviews={r.seed_key:r.id for r in session.scalars(select(Interview).where(
            Interview.college_id==college_id,Interview.seed_key.startswith("phase4:")))}
        existing_offers=set(session.scalars(select(Offer.seed_key).where(Offer.college_id==college_id,Offer.seed_key.startswith("phase4:"))))
        for offset in range(301,4797,200):
            pending_interviews=[];specs=[]
            for i in range(offset,min(offset+200,4797)):
                student=students.get(f"student{i:02d}@demo.jobjugaad.test")
                if student is None or student.resume_text!=f"Phase 4 synthetic resume {i}; demonstration only.":
                    continue  # Never fabricate outcomes on a real/pre-existing profile.
                p,meta=phase4_profile(i);job=jobs[titles[meta["track"]]]
                for n in range(max(meta["activity"],int(meta["selected"]))):
                    key=f"phase4:interview:{i}:{n}"
                    if key not in existing_interviews:
                        start=anchor-timedelta(days=3+i%12+n)
                        pending_interviews.append(dict(college_id=college_id,student_id=student.id,job_id=job.id,
                            scheduled_time=start,end_time=start+timedelta(minutes=30),venue=f"synthetic room {i}",panel_id=f"synthetic panel {i}",
                            status="selected" if meta["selected"] and n==0 else "completed",seed_key=key))
                if meta["selected"] and f"phase4:offer:{i}" not in existing_offers:
                    specs.append((i,student,job,meta))
            if pending_interviews:
                inserted=session.execute(insert(Interview).returning(Interview.id,Interview.seed_key),pending_interviews).all()
                existing_interviews.update({row.seed_key:row.id for row in inserted})
                created["interviews"]+=len(inserted)
            offer_values=[]
            for i,student,job,meta in specs:
                roll=meta["outcome_roll"]
                issued=roll>=0.12;accepted=roll>=0.35
                offer_values.append(dict(college_id=college_id,student_id=student.id,job_id=job.id,
                    interview_id=existing_interviews[f"phase4:interview:{i}:0"],ctc=job.ctc,is_synthetic=True,seed_key=f"phase4:offer:{i}",
                    offer_letter_status="issued" if issued else "draft",documents_status="submitted" if accepted else "pending",
                    verification_status="verified" if accepted else "pending",acceptance_status="accepted" if accepted else "declined" if roll>=0.25 else "pending",
                    joining_status="not_joined" if roll>=0.93 else "joined" if roll>=0.65 else "pending"))
            if offer_values:
                inserted=session.execute(insert(Offer).returning(Offer),offer_values).scalars().all()
                from engines.offers import snapshot
                session.execute(insert(OfferEvent),[dict(college_id=college_id,offer_id=o.id,actor_user_id=None,action="synthetic_import",
                    reason="Synthetic outcome sampled from proposed correlated data-generation assumptions; not a human decision or observed placement.",
                    snapshot={"before":None,"after":snapshot(o)}) for o in inserted])
                recipients={student.id:student.user_id for _,student,_,_ in specs}
                session.execute(insert(Notification),[dict(college_id=college_id,recipient_user_id=recipients[o.student_id],
                    event_key=f"offer:{o.id}:version:1",kind="offer",title="Synthetic offer tracking example",
                    body="Simulated offer history is available. These are fictional outcomes, not an actual employer offer.",
                    target_path="/student/offers") for o in inserted])
                created["offers"]+=len(inserted)
    return created


def seed_phase4(college_id=1):
    from sqlalchemy import func
    from models import Job,Match,Company
    from engines.talent import run_matching
    result=dict(students=seed_phase4_students(college_id),companies=seed_phase4_catalog(college_id))
    result.update(seed_phase4_outcomes(college_id))
    # Bring the original three drive snapshots up to the full population, preserving recruiter overrides.
    with tenant_session(college_id) as session:
        total=session.scalar(select(func.count()).select_from(Student).where(Student.college_id==college_id))
        jobs=session.scalars(select(Job).join(Company,Company.id==Job.company_id).join(User,User.id==Company.recruiter_user_id).where(
            Job.college_id==college_id,Company.college_id==college_id,User.college_id==college_id,
            User.email.in_([f"recruiter{i:02d}@demo.jobjugaad.test" for i in range(1,4)]),Job.title.in_([d.title for d in DEMO_DRIVES]))
            .order_by(Job.id).with_for_update(of=Job)).all()
        result["matching_runs"]=[]
        for job in jobs:
            covered=session.scalar(select(func.count()).select_from(Match).where(Match.college_id==college_id,Match.job_id==job.id))
            if covered<total:result["matching_runs"].append(run_matching(session,job).model_dump())
    return result


if __name__ == "__main__":
    initialize_schema()
    print(f"Created {seed_students()} synthetic students.")
    print(seed_companies())
    print(seed_phase3())
    print(seed_phase4())
