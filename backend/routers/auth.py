"""Student-only demo enrollment; role and tenant cannot be changed through profile input."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from auth import hash_password, verify_password, issue_token, student_session
from database import tenant_session
from models import User, Student
from schemas import SignupRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
# Equal-cost verification for nonexistent accounts avoids the obvious fast-failure path.
DUMMY_HASH = hash_password("unused-password-for-timing")

@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(payload: SignupRequest):
    try:
        with tenant_session(payload.college_id) as session:
            user = User(email=payload.email, password_hash=hash_password(payload.password),
                role="student", college_id=payload.college_id)
            session.add(user)
            session.flush()
            student = Student(user_id=user.id, college_id=user.college_id, name=payload.name)
            session.add(student)
            session.flush()
            return issue_token(user, student)
    except IntegrityError:
        raise HTTPException(409, "An account with this email already exists in this demo college.") from None

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    with tenant_session(payload.college_id) as session:
        user = session.scalar(select(User).where(User.email == payload.email, User.college_id == payload.college_id))
        valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
        if not user or not valid:
            raise HTTPException(401, "Email, password, or demo college is incorrect.")
        if user.role != "student":
            raise HTTPException(403, "Student access only in this phase.")
        student = session.scalar(select(Student).where(Student.user_id == user.id, Student.college_id == user.college_id))
        if student is None:
            raise HTTPException(404, "Student profile not found.")
        return issue_token(user, student)

@router.get("/me", response_model=UserResponse)
def me(context=Depends(student_session)):
    session, user = context
    student = session.scalar(select(Student).where(Student.user_id == user.id, Student.college_id == user.college_id))
    if student is None:
        raise HTTPException(404, "Student profile not found.")
    return UserResponse(user_id=user.id, student_id=student.id, college_id=user.college_id,
        email=user.email, name=student.name)
