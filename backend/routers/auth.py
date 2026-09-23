"""Role-specific demo enrollment; clients cannot assign themselves privileged roles."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from auth import hash_password, verify_password, issue_token, authenticated_session, user_response
from database import tenant_session
from admin_access import is_allowed_admin
from models import User, Student, Company
from schemas import SignupRequest, RecruiterSignupRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
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

@router.post("/recruiter/signup", response_model=TokenResponse, status_code=201)
def recruiter_signup(payload: RecruiterSignupRequest):
    try:
        with tenant_session(payload.college_id) as session:
            user = User(email=payload.email, password_hash=hash_password(payload.password),
                role="recruiter", college_id=payload.college_id)
            session.add(user)
            session.flush()
            company = Company(recruiter_user_id=user.id, college_id=user.college_id, **payload.company.model_dump())
            session.add(company)
            session.flush()
            return issue_token(user, company=company)
    except IntegrityError:
        raise HTTPException(409, "An account with this email already exists in this demo college.") from None

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    with tenant_session(payload.college_id) as session:
        user = session.scalar(select(User).where(User.email == payload.email, User.college_id == payload.college_id))
        valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
        if not user or not valid:
            raise HTTPException(401, "Email, password, or demo college is incorrect.")
        if user.role == "student":
            student = session.scalar(select(Student).where(Student.user_id == user.id, Student.college_id == user.college_id))
            if student is None:
                raise HTTPException(404, "Student profile not found.")
            return issue_token(user, student)
        if user.role == "recruiter":
            company = session.scalar(select(Company).where(Company.recruiter_user_id == user.id, Company.college_id == user.college_id))
            if company is None:
                raise HTTPException(404, "Company profile not found.")
            return issue_token(user, company=company)
        if user.role == "admin" and is_allowed_admin(user):
            return issue_token(user)
        raise HTTPException(403, "Administrator access is not enabled for this account.")

@router.get("/me", response_model=UserResponse)
def me(context=Depends(authenticated_session)):
    return user_response(*context)
