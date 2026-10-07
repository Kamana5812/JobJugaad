"""Single-use inbox recovery with tenant filters, quotas and session invalidation."""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import select, text, update
from database import tenant_session
from models import User, PasswordResetToken
from engines import email_delivery

GENERIC = {'detail': 'If this account exists in the selected college and email delivery is available, a reset link will be sent. Check your inbox and spam folder. Links expire in 30 minutes.'}


def request_reset(payload, background):
    # HMAC protects stored request addresses from simple offline dictionary lookup.
    from auth import signing_secret
    key = hmac.new(signing_secret().encode(), payload.email.encode(), hashlib.sha256).hexdigest()
    now = datetime.now(timezone.utc)
    with tenant_session(payload.college_id) as session:
        # Serialize quotas/issuance per tenant across workers; no untrusted proxy-IP assumptions.
        session.execute(text('SELECT pg_advisory_xact_lock(20261005, :college)'), {'college':payload.college_id})
        recent = session.scalars(select(PasswordResetToken).where(
            PasswordResetToken.college_id == payload.college_id,
            PasswordResetToken.created_at > now - timedelta(hours=1))).all()
        own = [row for row in recent if row.request_key == key]
        if len(recent) >= 60 or len(own) >= 3 or any(row.created_at > now - timedelta(minutes=1) for row in own):
            raise HTTPException(429, 'Please wait before requesting another reset. The limit is one per minute, three per hour per address, and sixty per hour per college.')
        user = session.scalar(select(User).where(User.college_id == payload.college_id,
            User.email == payload.email, User.disabled_at.is_(None)).with_for_update())
        raw = secrets.token_urlsafe(32)
        row = PasswordResetToken(college_id=payload.college_id, request_key=key,
            user_id=user.id if user else None, token_hash=hashlib.sha256(raw.encode()).hexdigest() if user else None,
            version_at_issue=user.token_version if user else None, expires_at=now + timedelta(minutes=30))
        from models import RecruiterBinding
        linked = user and session.scalar(select(RecruiterBinding.id).where(
            RecruiterBinding.college_id == payload.college_id, RecruiterBinding.user_id == user.id))
        deliver = bool(user and not linked and email_delivery.configured(user.email))
        if deliver:
            session.execute(update(PasswordResetToken).where(PasswordResetToken.college_id == payload.college_id,
                PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).values(used_at=now))
            row.delivery_status = 'pending'
        session.add(row); session.flush()
        identity = row.id
    # Never echo tokens or disclose account existence. Delivery is background work after commit.
    if deliver:
        background.add_task(deliver_reset, payload.college_id, identity, payload.email, raw)
    return GENERIC


def deliver_reset(college, identity, recipient, raw):
    link = f'https://jobjugaad.vercel.app/reset-password#college_id={college}&token={raw}'
    status = 'accepted'
    try:
        email_delivery.send_password_reset(recipient, link, f'password-reset:{college}:{identity}')
    except Exception:
        # Provider acceptance is not inbox delivery; ambiguous sends are never automatically retried.
        status = 'failed'
        logging.getLogger('jobjugaad').warning('Password recovery email delivery was not confirmed.')
    with tenant_session(college) as session:
        session.execute(update(PasswordResetToken).where(PasswordResetToken.college_id == college,
            PasswordResetToken.id == identity).values(delivery_status=status))


def reset_password(payload):
    from auth import hash_password
    digest = hashlib.sha256(payload.token.encode()).hexdigest()
    invalid = HTTPException(400, 'This reset link is invalid, expired or replaced. Request a new link.')
    with tenant_session(payload.college_id) as session:
        challenge = session.scalar(select(PasswordResetToken).where(
            PasswordResetToken.college_id == payload.college_id, PasswordResetToken.token_hash == digest))
        if challenge is None or challenge.user_id is None:
            raise invalid
        # User-first locking matches issuance and serializes separate valid links for the same user.
        user = session.scalar(select(User).where(User.college_id == payload.college_id,
            User.id == challenge.user_id).with_for_update())
        challenge = session.scalar(select(PasswordResetToken).where(PasswordResetToken.college_id == payload.college_id,
            PasswordResetToken.id == challenge.id).with_for_update().execution_options(populate_existing=True))
        now = datetime.now(timezone.utc)
        if user is None or user.disabled_at or challenge.used_at or challenge.expires_at <= now or challenge.version_at_issue != user.token_version:
            raise invalid
        from models import RecruiterBinding
        if session.scalar(select(RecruiterBinding.id).where(RecruiterBinding.college_id == payload.college_id, RecruiterBinding.user_id == user.id)):
            raise invalid
        session.execute(update(User).where(User.college_id == payload.college_id,
            User.id == user.id).values(password_hash=hash_password(payload.password), token_version=user.token_version + 1))
        session.execute(update(PasswordResetToken).where(PasswordResetToken.college_id == payload.college_id,
            PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).values(used_at=now))
    return {'detail': 'Password reset. All previous login sessions have been invalidated. Sign in with your new password and the same college.'}
