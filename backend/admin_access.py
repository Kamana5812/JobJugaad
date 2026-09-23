"""Server-configured admin access; no public admin signup or embedded credentials."""
import json
import os
from pydantic import TypeAdapter
from sqlalchemy import select, update
from database import tenant_session
from models import User
from schemas import AdminAccountConfig


def configured_accounts():
    accounts = TypeAdapter(list[AdminAccountConfig]).validate_python(json.loads(os.environ.get("ADMIN_ACCOUNTS", "[]")))
    if len(accounts) > 10:
        raise RuntimeError("ADMIN_ACCOUNTS supports at most ten explicit accounts.")
    return {(a.email.strip().lower(), a.college_id) for a in accounts}


def is_allowed_admin(user):
    return (user.email, user.college_id) in configured_accounts()


def provision_admin_accounts():
    count = 0
    for email, college in configured_accounts():
        with tenant_session(college) as session:
            user = session.scalar(select(User).where(User.email == email, User.college_id == college))
            if user is None:
                raise RuntimeError("An ADMIN_ACCOUNTS account does not exist. Register the account first, then redeploy.")
            if user.role != "admin":
                session.execute(update(User).where(User.id == user.id, User.college_id == college).values(role="admin"))
                count += 1
    return count
