"""Real college accounts require inbox verification and a recorded human approval."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, update, func, true
from models import User, Student, Company, AccountAccess, AccountAccessEvent, EmailVerificationToken
from schemas import AccountAccessResponse, AccessEventResponse, AccessQueueItem, AccessQueue
from colleges import college_name
from database import tenant_session
from engines import email_delivery
from engines.notifications import notify


def access_row(session, user, lock=False):
    query = select(AccountAccess).where(AccountAccess.college_id == user.college_id, AccountAccess.user_id == user.id)
    return session.scalar(query.with_for_update().execution_options(populate_existing=True) if lock else query)


def ensure_access(session, user):
    # Serialize first creation for older accounts without changing users or passwords.
    session.scalar(select(User).where(User.college_id == user.college_id, User.id == user.id).with_for_update())
    row = access_row(session, user, lock=True)
    if row is None:
        row = AccountAccess(college_id=user.college_id, user_id=user.id)
        session.add(row); session.flush()
    return row


def identity_fields(session, user):
    if user.college_id in (1, 2):
        return dict(is_demo=True, email_verified=False, access_status="legacy_demo")
    row = access_row(session, user) if session is not None else None
    verified = bool(row and row.email_verified_at)
    status = "unverified" if not verified else "approved" if user.role == "admin" else row.approval_status
    return dict(is_demo=False, email_verified=verified, access_status=status)


def require_access(session, user):
    if identity_fields(session, user)["access_status"] not in ("approved", "legacy_demo"):
        raise HTTPException(403, "Verify your email and obtain college administrator approval before using the placement workflow.")


def approved_scope(column, college, role):
    if college in (1, 2):
        return true()  # Archived demonstration tenants stay separate from real college records.
    return column.in_(select(User.id).join(AccountAccess,
        (AccountAccess.user_id == User.id) & (AccountAccess.college_id == User.college_id)).where(
        User.college_id == college, User.role == role, User.disabled_at.is_(None), AccountAccess.college_id == college,
        AccountAccess.email_verified_at.is_not(None), AccountAccess.approval_status == "approved"))


def event(session, user, row, action, reason):
    session.add(AccountAccessEvent(college_id=user.college_id, access_id=row.id,
        actor_user_id=user.id, action=action, reason=reason))
    session.flush()


def view(session, user, row=None):
    row = row or access_row(session, user)
    history = [] if row is None else session.scalars(select(AccountAccessEvent).where(
        AccountAccessEvent.college_id == user.college_id, AccountAccessEvent.access_id == row.id)
        .order_by(AccountAccessEvent.id)).all()
    return AccountAccessResponse(id=row.id if row else None, college_id=user.college_id,
        college_name=college_name(user.college_id), email=user.email, email_delivery_ready=email_delivery.configured(user.email),
        **identity_fields(session, user), affiliation_reference=row.affiliation_reference if row else "",
        context=row.context if row else "", version=row.version if row else 0,
        requested_at=row.requested_at if row else None,
        history=[AccessEventResponse.model_validate(h, from_attributes=True) for h in history])


def request_access(session, user, payload):
    if user.college_id in (1, 2) or user.role == "admin":
        raise HTTPException(409, "This account does not use public college approval requests.")
    row = ensure_access(session, user)
    if row.email_verified_at is None:
        raise HTTPException(403, "Verify your email before submitting a college access request.")
    if row.approval_status == "approved":
        raise HTTPException(409, "Your college access is already approved.")
    session.execute(update(AccountAccess).where(AccountAccess.college_id == user.college_id,
        AccountAccess.user_id == user.id, AccountAccess.id == row.id).values(
        affiliation_reference=payload.affiliation_reference, context=payload.context, approval_status="pending",
        requested_at=datetime.now(timezone.utc), version=row.version + 1))
    event(session, user, row, "requested", f"Affiliation reference: {payload.affiliation_reference}. Supporting context: {payload.context or 'Not provided'}. Account holder consented to college review.")
    return view(session, user, row)


def queue(session, admin, status, offset, limit):
    scope = (AccountAccess.college_id == admin.college_id, User.college_id == admin.college_id,
        User.role.in_(["student", "recruiter"]), AccountAccess.requested_at.is_not(None),
        AccountAccess.approval_status == status)
    query = select(AccountAccess, User).join(User,
        (User.id == AccountAccess.user_id) & (User.college_id == AccountAccess.college_id)).where(*scope)
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.execute(query.order_by(AccountAccess.requested_at, AccountAccess.id).offset(offset).limit(limit)).all()
    result = []
    for row, user in rows:
        model = Student if user.role == "student" else Company
        column = Student.user_id if user.role == "student" else Company.recruiter_user_id
        name = session.scalar(select(model.name).where(model.college_id == admin.college_id, column == user.id))
        result.append(AccessQueueItem(**view(session, user, row).model_dump(), name=name or "Account holder", role=user.role))
    return AccessQueue(items=result, total=total, offset=offset, limit=limit)


def review(session, admin, access_id, payload):
    row = session.scalar(select(AccountAccess).where(AccountAccess.college_id == admin.college_id,
        AccountAccess.id == access_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Account request not found.")
    user = session.scalar(select(User).where(User.college_id == admin.college_id, User.id == row.user_id))
    if user.role == "admin" or row.requested_at is None or row.email_verified_at is None:
        raise HTTPException(409, "Only submitted, email-verified student/recruiter requests can be reviewed.")
    if row.version != payload.version or row.approval_status == payload.status:
        raise HTTPException(409, "This request changed or already has that status. Refresh before reviewing.")
    session.execute(update(AccountAccess).where(AccountAccess.college_id == admin.college_id,
        AccountAccess.id == row.id, AccountAccess.version == payload.version).values(
        approval_status=payload.status, version=row.version + 1))
    event(session, admin, row, payload.status, payload.reason)
    notify(session, admin.college_id, user.id, f"account:{row.id}:{row.version}", "College access reviewed",
        f"Access {payload.status}. {payload.reason}", "/auth", "account")
    return view(session, user, row)


def request_verification(identity):
    now = datetime.now(timezone.utc)
    # Commit the hashed challenge before sending; no plaintext token is stored or returned by API.
    with tenant_session(identity["college_id"]) as session:
        user = session.scalar(select(User).where(User.college_id == identity["college_id"],
            User.id == identity["user_id"], User.role == identity["role"],
            User.token_version == identity.get('token_version', 0), User.disabled_at.is_(None)))
        if user is None:
            raise HTTPException(401, "Your session was invalidated. Please log in again.")
        if user.college_id in (1, 2):
            raise HTTPException(403, "Use a real college account for email verification.")
        if not email_delivery.configured(user.email):
            raise HTTPException(503, "Email delivery is unavailable for this account. The default Resend sender is limited to the service owner's test inbox; other users need a verified sending domain.")
        row = ensure_access(session, user)
        if row.email_verified_at:
            raise HTTPException(409, "This email address is already verified.")
        if row.last_email_requested_at and (now - row.last_email_requested_at).total_seconds() < 60:
            raise HTTPException(429, "Please wait one minute before requesting another verification email.")
        count = session.scalar(select(func.count()).select_from(EmailVerificationToken).where(
            EmailVerificationToken.college_id == user.college_id, EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.created_at > now - timedelta(days=1)))
        if count >= 10:
            raise HTTPException(429, "Daily verification email limit reached. Please retry tomorrow.")
        session.execute(update(EmailVerificationToken).where(EmailVerificationToken.college_id == user.college_id,
            EmailVerificationToken.user_id == user.id, EmailVerificationToken.used_at.is_(None)).values(used_at=now))
        raw = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        token = EmailVerificationToken(college_id=user.college_id, user_id=user.id, token_hash=hashed,
            expires_at=now + timedelta(hours=1))
        session.add(token)
        session.execute(update(AccountAccess).where(AccountAccess.college_id == user.college_id,
            AccountAccess.user_id == user.id).values(last_email_requested_at=now))
        session.flush()
        recipient = user.email
        key = f"verification:{user.college_id}:{token.id}"
        link = f"https://jobjugaad.vercel.app/verify-email#college_id={user.college_id}&token={raw}"
    email_delivery.send_verification(recipient, link, key)
    return {"detail": "Verification email requested. Check your inbox and spam folder; the link expires in one hour."}


def verify_email(payload):
    hashed = hashlib.sha256(payload.token.encode()).hexdigest()
    with tenant_session(payload.college_id) as session:
        # Lock user/access first, same ordering as resend; avoids deadlocks with token invalidation.
        challenge = session.scalar(select(EmailVerificationToken).where(
            EmailVerificationToken.college_id == payload.college_id, EmailVerificationToken.token_hash == hashed))
        if challenge is None:
            raise HTTPException(400, "This verification link is invalid. Request a new email.")
        user = session.scalar(select(User).where(User.college_id == payload.college_id, User.id == challenge.user_id))
        row = ensure_access(session, user)
        challenge = session.scalar(select(EmailVerificationToken).where(EmailVerificationToken.college_id == payload.college_id,
            EmailVerificationToken.id == challenge.id).with_for_update().execution_options(populate_existing=True))
        if challenge.used_at:
            if row.email_verified_at:
                return {"detail": "Email already verified. Sign in to continue college approval."}
            raise HTTPException(400, "This verification link was replaced. Request a new email.")
        now = datetime.now(timezone.utc)
        if challenge.expires_at <= now:
            raise HTTPException(410, "This verification link expired. Request a new email.")
        session.execute(update(EmailVerificationToken).where(EmailVerificationToken.college_id == payload.college_id,
            EmailVerificationToken.id == challenge.id).values(used_at=now))
        session.execute(update(AccountAccess).where(AccountAccess.college_id == payload.college_id,
            AccountAccess.id == row.id).values(email_verified_at=now, version=row.version + 1))
        event(session, user, row, "email_verified", "Account holder confirmed access to their registered email inbox.")
    return {"detail": "Email verified. Sign in and submit your college access request."}
