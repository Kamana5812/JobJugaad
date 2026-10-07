"""Owned exports and human-reviewed account closure; retained workflow is explicit."""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update
from sqlalchemy.inspection import inspect
from models import User, Student, Company, DataRequest, AccountAccess, AccountAccessEvent, Notification
from database import Base
from schemas import DataRequestResponse, AccountExportResponse

EXPLANATION = ('A restriction closes sign-in and revokes sessions. Placement/audit records are retained for administrator erasure review; '
    'it does not mean all data or backup copies have been deleted. Review is due within 30 days.')

def view(row):
    return DataRequestResponse(id=row.id, user_id=row.user_id,status=row.status,reason=row.reason,
        review_reason=row.review_reason,created_at=row.created_at,reviewed_at=row.reviewed_at,
        retention_until=row.retention_until,explanation=EXPLANATION)

def requests(session,user,admin=False):
    query=select(DataRequest).where(DataRequest.college_id==user.college_id)
    if not admin: query=query.where(DataRequest.user_id==user.id)
    return [view(row) for row in session.scalars(query.order_by(DataRequest.id.desc()).limit(100)).all()]

def create(session,user,payload):
    session.scalar(select(User).where(User.college_id==user.college_id,User.id==user.id).with_for_update())
    existing=session.scalar(select(DataRequest).where(DataRequest.college_id==user.college_id,
        DataRequest.user_id==user.id,DataRequest.status.in_(['requested','restricted_pending_erasure'])))
    if existing: raise HTTPException(409,'A deletion review is already open for your account.')
    row=DataRequest(college_id=user.college_id,user_id=user.id,reason=payload.reason)
    session.add(row);session.flush()
    return view(row)

def withdraw(session,user,identity):
    row=session.scalar(select(DataRequest).where(DataRequest.college_id==user.college_id,
        DataRequest.user_id==user.id,DataRequest.id==identity).with_for_update())
    if row is None: raise HTTPException(404,'Request not found.')
    if row.status!='requested': raise HTTPException(409,'Only a pending request can be withdrawn.')
    row.status='withdrawn';return view(row)

def review(session,admin,identity,payload):
    row=session.scalar(select(DataRequest).where(DataRequest.college_id==admin.college_id,DataRequest.id==identity).with_for_update())
    if row is None: raise HTTPException(404,'Request not found.')
    if row.status!='requested': raise HTTPException(409,'This request has already been reviewed.')
    user=session.scalar(select(User).where(User.college_id==admin.college_id,User.id==row.user_id).with_for_update())
    if user.role=='admin' and payload.action=='restrict':
        raise HTTPException(409,'Administrator closure requires an owner-managed successor and continuity review. This endpoint cannot close administrator accounts.')
    now=datetime.now(timezone.utc)
    row.status='restricted_pending_erasure' if payload.action=='restrict' else 'rejected'
    row.review_reason=payload.reason;row.reviewed_by=admin.id;row.reviewed_at=now
    if payload.action=='restrict':
        row.retention_until=now+timedelta(days=30)
        session.execute(update(User).where(User.college_id==admin.college_id,User.id==user.id)
            .values(disabled_at=now,token_version=User.token_version+1))
        access=session.scalar(select(AccountAccess).where(AccountAccess.college_id==admin.college_id,AccountAccess.user_id==user.id).with_for_update())
        if access:
            access.approval_status='rejected';access.version+=1
            session.add(AccountAccessEvent(college_id=admin.college_id,access_id=access.id,actor_user_id=admin.id,
                action='rejected',reason='Account restricted following deletion review: '+payload.reason))
    session.flush();return view(row)

def export_account(session,user):
    from models import Job, RecruiterWorkspace, RecruiterBinding
    student=session.scalar(select(Student).where(Student.college_id==user.college_id,Student.user_id==user.id))
    company=session.scalar(select(Company).where(Company.college_id==user.college_id,Company.recruiter_user_id==user.id))
    records={}
    # Allowlist owner relationships. No matches/candidate snapshots are exported to a recruiter.
    for mapper in Base.registry.mappers:
        model=mapper.class_;name=model.__tablename__
        condition=None
        if name in ('students','companies'): condition=model.id==(student.id if name=='students' and student else company.id if name=='companies' and company else -1)
        elif student and 'student_id' in mapper.columns: condition=model.student_id==student.id
        elif model in (DataRequest,AccountAccess): condition=model.user_id==user.id
        elif model==Notification: condition=model.recipient_user_id==user.id
        elif model==Job and company: condition=model.company_id==company.id
        elif model==RecruiterWorkspace and company: condition=model.home_user_id==user.id
        elif model==RecruiterBinding and company: condition=model.user_id==user.id
        if condition is None: continue
        rows=session.scalars(select(model).where(model.college_id==user.college_id,condition)).all()
        fields=[c.key for c in inspect(model).columns if c.key not in ('password_hash','token_hash','request_key','readiness_score')]
        records[name]=[jsonable_encoder({key:getattr(row,key) for key in fields}) for row in rows]
    return AccountExportResponse(exported_at=datetime.now(timezone.utc),college_id=user.college_id,
        account={'user_id':user.id,'email':user.email,'role':user.role,'created_at':user.created_at},records=records,
        explanation='Your account and directly owned records only. Authentication secrets and other candidates are excluded. Private offer PDFs use the existing authenticated download workflow; this JSON export does not include their file bytes. Audit actors appear as IDs, not other account details.')
