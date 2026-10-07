"""Home-account authentication with independently approved, RLS-scoped campus workspaces."""
import secrets
from contextlib import contextmanager
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from database import tenant_session
from models import User, Company, RecruiterBinding, RecruiterWorkspace
from engines import accounts
from colleges import college_name, valid_college


def binding(session, user):
    return session.scalar(select(RecruiterBinding).where(
        RecruiterBinding.college_id == user.college_id, RecruiterBinding.user_id == user.id))


@contextmanager
def home_context(context):
    session, user = context
    if user.role != 'recruiter':
        raise HTTPException(403, 'Recruiter accounts only.')
    link = binding(session, user)
    college = link.home_college_id if link else user.college_id
    identity = link.home_user_id if link else user.id
    if college in (1, 2):
        raise HTTPException(403, 'Use a verified real-college recruiter account for multiple workspaces.')
    with tenant_session(college) as home:
        owner = home.scalar(select(User).where(User.college_id == college,
            User.id == identity, User.role == 'recruiter', User.disabled_at.is_(None)))
        if owner is None:
            raise HTTPException(401, 'Your home account is unavailable. Sign in again.')
        yield home, owner


def list_workspaces(context):
    active_college = context[1].college_id
    with home_context(context) as (session, owner):
        result = [dict(college_id=owner.college_id, college_name=college_name(owner.college_id),
            access_status=accounts.identity_fields(session, owner)['access_status'],
            is_home=True, active=active_college == owner.college_id)]
        links = session.scalars(select(RecruiterWorkspace).where(
            RecruiterWorkspace.college_id == owner.college_id,
            RecruiterWorkspace.home_user_id == owner.id).order_by(RecruiterWorkspace.target_college_id)).all()
        for link in links:
            # Each read opens only the explicitly linked tenant; no RLS bypass or global query.
            with tenant_session(link.target_college_id) as target:
                local = target.scalar(select(User).where(User.college_id == link.target_college_id,
                    User.id == link.target_user_id, User.role == 'recruiter'))
                status = 'unavailable' if local is None or local.disabled_at else accounts.identity_fields(target, local)['access_status']
                result.append(dict(college_id=link.target_college_id, college_name=college_name(link.target_college_id),
                    access_status=status, is_home=False, active=active_college == link.target_college_id))
        return dict(home_college_id=owner.college_id, items=result)


def request_workspace(context, payload):
    from auth import hash_password
    try:
        with home_context(context) as (session, owner):
            session.scalar(select(User).where(User.college_id == owner.college_id,
                User.id == owner.id).with_for_update())
            access = accounts.access_row(session, owner)
            if access is None or access.email_verified_at is None:
                raise HTTPException(403, 'Verify your home account email before requesting a college workspace.')
            if payload.college_id == owner.college_id:
                accounts.request_access(session, owner, payload)
                return
            directory = session.scalar(select(RecruiterWorkspace).where(
                RecruiterWorkspace.college_id == owner.college_id,
                RecruiterWorkspace.home_user_id == owner.id,
                RecruiterWorkspace.target_college_id == payload.college_id))
            company = session.scalar(select(Company).where(Company.college_id == owner.college_id,
                Company.recruiter_user_id == owner.id))
            if company is None:
                raise HTTPException(404, 'Your home company profile is missing.')
            home_college, home_user = owner.college_id, owner.id
            email, name, industry, verified_at = owner.email, company.name, company.industry, access.email_verified_at
            # One transaction switches tenant scope only after home ownership is checked.
            # Every ORM operation also carries an explicit college_id predicate/value.
            session.flush()
            session.execute(text("SELECT set_config('app.college_id', :tenant, true)"), {'tenant': str(payload.college_id)})
            if directory:
                local = session.scalar(select(User).where(User.college_id == payload.college_id,
                    User.id == directory.target_user_id, User.disabled_at.is_(None)))
                if local is None:
                    raise HTTPException(409, 'This workspace is unavailable; contact its college administrator.')
            else:
                existing = session.scalar(select(User.id).where(User.college_id == payload.college_id, User.email == email))
                if existing:
                    # Email equality is not proof of ownership; never merge or adopt an existing account.
                    raise HTTPException(409, 'An account already exists at that college. Contact support; existing accounts are never linked by email alone.')
                local = User(college_id=payload.college_id, email=email, role='recruiter',
                    password_hash=hash_password(secrets.token_urlsafe(40)))
                session.add(local); session.flush()
                session.add(Company(college_id=payload.college_id, recruiter_user_id=local.id, name=name, industry=industry))
                session.add(RecruiterBinding(college_id=payload.college_id, user_id=local.id,
                    home_college_id=home_college, home_user_id=home_user))
                row = accounts.ensure_access(session, local)
                row.email_verified_at = verified_at
                session.flush()
                accounts.event(session, local, row, 'home_email_verified',
                    'Inbox verification inherited from the authenticated home recruiter account; college approval remains independent.')
            accounts.request_access(session, local, payload)
            local_id = local.id
            session.flush()
            session.execute(text("SELECT set_config('app.college_id', :tenant, true)"), {'tenant': str(home_college)})
            if directory is None:
                session.add(RecruiterWorkspace(college_id=home_college, home_user_id=home_user,
                    target_college_id=payload.college_id, target_user_id=local_id))
                session.flush()
    except IntegrityError:
        raise HTTPException(409, 'This workspace request conflicts with an existing account. Refresh and retry.') from None


def switch_workspace(context, college):
    from auth import issue_token
    if not valid_college(college) or college in (1, 2):
        raise HTTPException(422, 'Choose a listed real college.')
    with home_context(context) as (session, owner):
        if college == owner.college_id:
            company = session.scalar(select(Company).where(Company.college_id == college, Company.recruiter_user_id == owner.id))
            return issue_token(owner, company=company, session=session)
        if not accounts.identity_fields(session, owner)['email_verified']:
            raise HTTPException(403, 'Verify your home email first.')
        link = session.scalar(select(RecruiterWorkspace).where(RecruiterWorkspace.college_id == owner.college_id,
            RecruiterWorkspace.home_user_id == owner.id, RecruiterWorkspace.target_college_id == college))
        if link is None:
            raise HTTPException(404, 'Request access to this college first.')
        with tenant_session(college) as target:
            local = target.scalar(select(User).where(User.college_id == college, User.id == link.target_user_id,
                User.role == 'recruiter', User.disabled_at.is_(None)))
            if local is None:
                raise HTTPException(403, 'This college workspace is unavailable.')
            accounts.require_access(target, local)
            company = target.scalar(select(Company).where(Company.college_id == college, Company.recruiter_user_id == local.id))
            return issue_token(local, company=company, session=target,
                home_identity={'home_college_id': owner.college_id, 'home_user_id': owner.id, 'home_token_version': owner.token_version})
