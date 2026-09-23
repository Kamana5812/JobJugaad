"""JWT identity and bcrypt; role, tenant and ownership are enforced separately."""
import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from database import tenant_session
from admin_access import is_allowed_admin
from models import User, Student, Company
from schemas import UserResponse, TokenResponse

passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
TOKEN_SECONDS = 7200
ISSUER = "jobjugaad"
# Preserve the existing token audience so Phase 1 sessions remain valid.
# Authorization uses the verified role claim plus the current database role.
AUDIENCE = "jobjugaad-student"

def signing_secret():
    secret = os.environ.get("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters.")
    return secret

def hash_password(password):
    return passwords.hash(password)

def verify_password(password, hashed):
    return passwords.verify(password, hashed)

def user_response(session, user):
    if user.role == "admin":
        return UserResponse(user_id=user.id, college_id=user.college_id, role="admin",
            email=user.email, name="Placement administrator")
    if user.role == "student":
        student = session.scalar(select(Student).where(Student.user_id == user.id, Student.college_id == user.college_id))
        if student is None:
            raise HTTPException(404, "Student profile not found.")
        return UserResponse(user_id=user.id, student_id=student.id, college_id=user.college_id,
            role=user.role, email=user.email, name=student.name)
    company = session.scalar(select(Company).where(Company.recruiter_user_id == user.id, Company.college_id == user.college_id))
    if company is None:
        raise HTTPException(404, "Company profile not found.")
    return UserResponse(user_id=user.id, company_id=company.id, college_id=user.college_id,
        role=user.role, email=user.email, name=company.name)

def issue_token(user, student=None, company=None):
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": str(user.id), "user_id": user.id, "role": user.role,
        "college_id": user.college_id, "iat": now, "exp": now + timedelta(seconds=TOKEN_SECONDS),
        "iss": ISSUER, "aud": AUDIENCE}, signing_secret(), algorithm="HS256")
    return TokenResponse(access_token=token, expires_in=TOKEN_SECONDS,
        user=UserResponse(user_id=user.id, student_id=student.id if student else None,
            company_id=company.id if company else None, college_id=user.college_id,
            role=user.role, email=user.email, name=student.name if student else company.name if company else "Placement administrator"))

def current_identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    unauthorized = HTTPException(401, "Please log in again; your session is missing or expired.",
        headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    try:
        claims = jwt.decode(credentials.credentials, signing_secret(), algorithms=["HS256"],
            issuer=ISSUER, audience=AUDIENCE, options={"require_exp": True, "require_iat": True, "require_sub": True})
        if (type(claims.get("college_id")) is not int or claims["college_id"] not in (1, 2)
            or type(claims.get("user_id")) is not int or claims["user_id"] < 1
            or claims["sub"] != str(claims["user_id"])):
            raise unauthorized
        if claims.get("role") not in ("student", "recruiter", "admin"):
            raise HTTPException(403, "This role is not available in the current phase.")
        return claims
    except JWTError:
        raise unauthorized from None

def authenticated_session(identity=Depends(current_identity)):
    with tenant_session(identity["college_id"]) as session:
        user = session.scalar(select(User).where(User.id == identity["user_id"],
            User.college_id == identity["college_id"], User.role == identity["role"]))
        if user is None:
            raise HTTPException(401, "Your account or role has changed. Please log in again.")
        if user.role == "admin" and not is_allowed_admin(user):
            raise HTTPException(403, "Administrator access is not enabled for this account.")
        yield session, user

def student_session(context=Depends(authenticated_session)):
    if context[1].role != "student":
        raise HTTPException(403, "This endpoint is available to students only.")
    return context

def recruiter_session(context=Depends(authenticated_session)):
    if context[1].role != "recruiter":
        raise HTTPException(403, "This endpoint is available to recruiters only.")
    return context

def owned_student(session, user, student_id):
    student = session.scalar(select(Student).where(Student.id == student_id,
        Student.college_id == user.college_id, Student.user_id == user.id))
    if student is None:
        raise HTTPException(404, "Student profile not found.")
    return student

def admin_session(context=Depends(authenticated_session)):
    if context[1].role != "admin":
        raise HTTPException(403, "This endpoint is available to placement administrators only.")
    return context
