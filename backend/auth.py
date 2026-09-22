"""JWT identity and bcrypt password hashing; never trust tenant IDs from profile input."""
import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from database import tenant_session
from models import User, Student
from schemas import UserResponse, TokenResponse

passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
TOKEN_SECONDS = 7200
ISSUER = "jobjugaad"
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

def issue_token(user, student):
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": str(user.id), "user_id": user.id, "role": user.role,
        "college_id": user.college_id, "iat": now, "exp": now + timedelta(seconds=TOKEN_SECONDS),
        "iss": ISSUER, "aud": AUDIENCE}, signing_secret(), algorithm="HS256")
    return TokenResponse(access_token=token, expires_in=TOKEN_SECONDS,
        user=UserResponse(user_id=user.id, student_id=student.id, college_id=user.college_id,
            role=user.role, email=user.email, name=student.name))

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
        if claims.get("role") != "student":
            raise HTTPException(403, "This endpoint is available to students only.")
        return claims
    except JWTError:
        raise unauthorized from None

def student_session(identity=Depends(current_identity)):
    with tenant_session(identity["college_id"]) as session:
        user = session.scalar(select(User).where(User.id == identity["user_id"],
            User.college_id == identity["college_id"], User.role == "student"))
        if user is None:
            raise HTTPException(401, "Your account is no longer available. Please log in again.")
        yield session, user

def owned_student(session, user, student_id):
    student = session.scalar(select(Student).where(Student.id == student_id,
        Student.college_id == user.college_id, Student.user_id == user.id))
    if student is None:
        raise HTTPException(404, "Student profile not found.")
    return student
