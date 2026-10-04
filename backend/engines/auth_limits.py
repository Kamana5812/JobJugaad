"""Database-backed address and college limits; no reliance on untrusted forwarded IPs."""
import hashlib
import hmac
import os
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from sqlalchemy import select, text
from database import engine, tenant_session
from models import AuthLimit
from colleges import valid_college

def consume(college, email, operation):
    from auth import signing_secret
    period = 900 if operation == 'login' else 3600
    window = datetime.fromtimestamp(int(datetime.now(timezone.utc).timestamp()) // period * period, timezone.utc)
    quotas = [(operation + ':' + email, 8 if operation == 'login' else 3), (operation + ':college', 1000 if operation == 'login' else 200)]
    # Only explicitly authorized loopback test databases get high fixture quotas.
    testing = os.environ.get('ALLOW_TEST_DATABASE') == 'yes' and engine.url.host in ('127.0.0.1','localhost')
    exhausted = False
    with tenant_session(college) as session:
        session.execute(text('SELECT pg_advisory_xact_lock(20261006, :college)'), {'college':college})
        for identity, limit in quotas:
            key = hmac.new(signing_secret().encode(), identity.encode(), hashlib.sha256).hexdigest()
            row = session.scalar(select(AuthLimit).where(AuthLimit.college_id == college,
                AuthLimit.request_key == key, AuthLimit.window_start == window))
            if row is None:
                row=AuthLimit(college_id=college, request_key=key, window_start=window, attempts=0)
                session.add(row)
            maximum = 100000 if testing else limit
            if row.attempts >= maximum:
                exhausted = True
            else:
                row.attempts += 1
    if exhausted:
        retry = max(1, int(window.timestamp()) + period - int(datetime.now(timezone.utc).timestamp()))
        raise HTTPException(429, 'Too many account requests. Please wait before trying again.', headers={'Retry-After':str(retry)})

async def enforce(request: Request):
    payload = await request.json()
    college = payload.get('college_id') if isinstance(payload,dict) else None
    email = payload.get('email') if isinstance(payload,dict) else None
    if valid_college(college) and isinstance(email,str) and len(email) <= 254:
        consume(college, email.strip().lower(), 'login' if request.url.path.endswith('/login') else 'signup')
