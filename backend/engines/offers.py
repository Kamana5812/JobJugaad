"""Explicit offer stages with role-scoped actions, version checks and audit history."""
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update, func, text, exists
from models import Offer, OfferEvent, Interview, Student, Job, Company
from schemas import OfferResponse, OfferAuditResponse, OfferList, OfferCandidate, OfferCandidateList
from engines.notifications import notify_student, notify_admins

STAGES = ("offer_letter_status","documents_status","verification_status","acceptance_status","joining_status")
METHOD = ("Recorded lifecycle statuses only. Document submission and verification are human declarations; "
    "no offer letter/document files are uploaded or automatically validated here. Notifications are simulated in-app only.")


def snapshot(row):
    return dict(id=row.id, student_id=row.student_id, job_id=row.job_id, interview_id=row.interview_id,
        ctc=float(row.ctc), version=row.version, **{key:getattr(row,key) for key in STAGES})


def next_steps(row):
    if row.offer_letter_status == "withdrawn":
        return ["Offer withdrawn. Contact the placement cell for context and other opportunities."]
    if row.joining_status == "joined":
        return ["Joining recorded. This does not track later career outcomes."]
    if row.joining_status == "not_joined":
        return ["Non-joining recorded. Contact the placement cell to review other opportunities."]
    if row.acceptance_status == "declined":
        return ["Student declined this offer. Discuss other opportunities with the placement cell."]
    steps=[]
    if row.offer_letter_status == "draft":
        steps.append("Administrator: record offer letter issuance before the student responds.")
    if row.documents_status != "submitted":
        steps.append("Student: submit documents through the college's agreed channel, then record submission here.")
    elif row.verification_status != "verified":
        steps.append("Administrator: review documents outside this prototype and record verification or required corrections.")
    if row.offer_letter_status == "issued" and row.acceptance_status == "pending":
        steps.append("Student: review the offer and record your acceptance or decline.")
    if row.acceptance_status == "accepted" and row.verification_status == "verified":
        steps.append("Administrator: confirm whether joining occurred and record the outcome.")
    return steps


def offer_rows(session, user):
    query = select(Offer).where(Offer.college_id == user.college_id)
    if user.role == "student":
        query = query.join(Student, Student.id == Offer.student_id).where(
            Student.college_id == user.college_id, Student.user_id == user.id)
    elif user.role != "admin":
        raise HTTPException(403, "Offer tracking is available to students and placement administrators.")
    return query


def owned_offer(session, user, identity):
    row = session.scalar(offer_rows(session,user).where(Offer.id == identity).with_for_update(of=Offer))
    if row is None:
        raise HTTPException(404, "Offer not found.")
    return row


def responses(session, college, rows):
    names = {}
    ids = [row.id for row in rows]
    for offer, student, job, company in session.execute(select(Offer,Student,Job,Company)
            .join(Student,Student.id == Offer.student_id).join(Job,Job.id == Offer.job_id).join(Company,Company.id == Job.company_id)
            .where(Offer.college_id == college,Offer.id.in_(ids),Student.college_id == college,
                Job.college_id == college,Company.college_id == college)):
        names[offer.id] = (student.name,job.title,company.name)
    audits = defaultdict(list)
    for event in session.scalars(select(OfferEvent).where(OfferEvent.college_id == college,OfferEvent.offer_id.in_(ids)).order_by(OfferEvent.id)):
        audits[event.offer_id].append(OfferAuditResponse.model_validate(event,from_attributes=True))
    return [OfferResponse(**snapshot(row),student_name=names[row.id][0],job_title=names[row.id][1],
        company_name=names[row.id][2],is_synthetic=row.is_synthetic,created_at=row.created_at,updated_at=row.updated_at,
        next_steps=next_steps(row),audit=audits[row.id],methodology=METHOD) for row in rows]


def list_offers(session, user, offset=0, limit=20):
    query = offer_rows(session,user)
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.scalars(query.order_by(Offer.id.desc()).offset(offset).limit(limit)).all()
    return OfferList(offers=responses(session,user.college_id,rows),total=total,offset=offset,limit=limit)


def candidates(session, user, search="", offset=0, limit=20):
    college=user.college_id
    already_offered = exists(select(Offer.id).where(Offer.college_id == college,
        Offer.student_id == Interview.student_id,Offer.job_id == Interview.job_id))
    query = select(Interview,Student,Job).join(Student,Student.id == Interview.student_id).join(Job,Job.id == Interview.job_id).where(
        Interview.college_id == college,Student.college_id == college,Job.college_id == college,
        Interview.status == "selected",~already_offered)
    if search:
        query=query.where(Student.name.icontains(search,autoescape=True))
    total=session.scalar(select(func.count()).select_from(query.subquery()))
    rows=session.execute(query.order_by(Interview.id.desc()).offset(offset).limit(limit)).all()
    return OfferCandidateList(candidates=[OfferCandidate(interview_id=i.id,student_id=s.id,student_name=s.name,
        job_title=j.title,ctc=float(j.ctc)) for i,s,j in rows],total=total,offset=offset,limit=limit)


def record_change(session, user, row, action, reason, before):
    session.add(OfferEvent(college_id=user.college_id,offer_id=row.id,actor_user_id=user.id,
        action=action,reason=reason,snapshot={"before":before,"after":snapshot(row)}))
    message = f"Offer #{row.id}: {action.replace('_',' ')}. Recorded reason: {reason}"
    key=f"offer:{row.id}:version:{row.version}"
    notify_student(session,user.college_id,row.student_id,key,"Offer tracking update",message,"offer")
    if user.role == "student":
        notify_admins(session,user.college_id,key,"Student offer response",message)
    session.flush()
    return responses(session,user.college_id,[row])[0]


def create_offer(session, user, payload):
    # Serialize creation per college so different selected interviews cannot create duplicate student/job offers.
    session.execute(text("SELECT pg_advisory_xact_lock(20260401, :college)"),{"college":user.college_id})
    interview=session.scalar(select(Interview).where(Interview.college_id == user.college_id,
        Interview.id == payload.interview_id).with_for_update())
    if interview is None:
        raise HTTPException(404,"Selected interview not found.")
    if interview.status != "selected":
        raise HTTPException(409,"Record the interview as selected before creating an offer.")
    if session.scalar(select(Offer.id).where(Offer.college_id == user.college_id,
            Offer.student_id == interview.student_id,Offer.job_id == interview.job_id)):
        raise HTTPException(409,"An offer already exists for this student and drive.")
    job=session.scalar(select(Job).where(Job.college_id == user.college_id,Job.id == interview.job_id))
    row=Offer(college_id=user.college_id,student_id=interview.student_id,job_id=job.id,
        interview_id=interview.id,ctc=payload.ctc if payload.ctc is not None else job.ctc)
    session.add(row);session.flush()
    return record_change(session,user,row,"offer_created",payload.reason,None)


def check_version(row, version):
    if row.version != version:
        raise HTTPException(409,"This offer changed. Refresh its stages before submitting another action.")
    if row.offer_letter_status == "withdrawn" or row.joining_status != "pending" or row.acceptance_status == "declined":
        raise HTTPException(409,"This offer is closed; its history remains available.")


def save_change(session,user,row,values,action,reason):
    before=snapshot(row)
    session.execute(update(Offer).where(Offer.college_id == user.college_id,Offer.id == row.id,
        Offer.version == row.version).values(**values,version=row.version+1,updated_at=datetime.now(timezone.utc)))
    return record_change(session,user,row,action,reason,before)


def admin_update(session,user,identity,payload):
    row=owned_offer(session,user,identity);check_version(row,payload.version)
    stage,value=payload.stage,payload.value
    changes={stage:value}
    valid=False
    if stage == "offer_letter_status":
        valid=(row.offer_letter_status == "draft" and value in ("issued","withdrawn")) or (row.offer_letter_status == "issued" and value == "withdrawn")
    elif stage == "documents_status":
        valid=row.offer_letter_status == "issued" and row.documents_status == "submitted" and value == "changes_requested"
        changes["verification_status"]="pending"
    elif stage == "verification_status":
        valid=row.offer_letter_status == "issued" and row.documents_status == "submitted" and value in ("verified","rejected") and value != row.verification_status
    elif stage == "joining_status":
        valid=(row.offer_letter_status == "issued" and row.acceptance_status == "accepted" and row.verification_status == "verified"
            and value in ("joined","not_joined"))
    if not valid:
        raise HTTPException(409,"That stage change is not available. Issue the letter, obtain the student's response and document submission, then verify before recording joining.")
    return save_change(session,user,row,changes,f"{stage}:{value}",payload.reason)


def student_action(session,user,identity,payload):
    row=owned_offer(session,user,identity);check_version(row,payload.version)
    if row.offer_letter_status != "issued":
        raise HTTPException(409,"Wait for the administrator to record the issued offer letter.")
    if payload.action == "submit_documents":
        if row.documents_status not in ("pending","changes_requested"):
            raise HTTPException(409,"Document submission is already recorded.")
        changes=dict(documents_status="submitted",verification_status="pending")
    else:
        if row.acceptance_status != "pending":
            raise HTTPException(409,"Your offer response has already been recorded.")
        changes=dict(acceptance_status="accepted" if payload.action == "accept" else "declined")
    return save_change(session,user,row,changes,payload.action,payload.reason)
