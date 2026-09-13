'''Pydantic schemas for request validation and response models.
These mirror the ORM models where needed and omit internal fields such as
password hashes.
'''

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(student|recruiter|admin)$")
    college_id: uuid.UUID

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    college_id: uuid.UUID
    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class StudentRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    branch: Optional[str]
    cgpa: Optional[float]
    backlog_count: Optional[int]
    resume_text: Optional[str]
    technical_score: Optional[float]
    project_score: Optional[float]
    aptitude_score: Optional[float]
    communication_score: Optional[float]
    interview_score: Optional[float]
    readiness_score: Optional[float]
    college_id: uuid.UUID
    class Config:
        orm_mode = True

class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None

class CompanyRead(BaseModel):
    id: uuid.UUID
    recruiter_user_id: uuid.UUID
    name: str
    industry: Optional[str]
    college_id: uuid.UUID
    class Config:
        orm_mode = True

class JobCreate(BaseModel):
    title: str
    ctc: Optional[float] = None
    min_cgpa: Optional[float] = None
    eligible_branches: Optional[List[str]] = None
    required_skills: Optional[Dict[str, int]] = None

class JobRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    ctc: Optional[float]
    min_cgpa: Optional[float]
    eligible_branches: Optional[List[str]]
    required_skills: Optional[Dict[str, int]]
    college_id: uuid.UUID
    class Config:
        orm_mode = True

class MatchRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    student_id: uuid.UUID
    match_score: float
    factor_breakdown: Optional[Dict[str, float]] = None
    missing_requirements: Optional[Dict[str, any]] = None
    explanation: Optional[str] = None
    override_status: Optional[str] = None
    class Config:
        orm_mode = True

class ReadinessResponse(BaseModel):
    score: float
    band: str
    breakdown: Dict[str, float]
    explanation: str
    class Config:
        orm_mode = True

class MatchOverride(BaseModel):
    status: str

class InterviewCreate(BaseModel):
    job_id: uuid.UUID
    student_id: uuid.UUID
    preferred_start: str  # ISO string
    duration_minutes: int
    venue: str
    panel: str

class InterviewRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    student_id: uuid.UUID
    start_time: str
    end_time: str
    venue: str
    panel: str
    college_id: uuid.UUID
    class Config:
        orm_mode = True

class AtRiskStudent(BaseModel):
    student_id: str
    student_name: str
    is_at_risk: bool
    factors: List[str]
    recommendation: Optional[str] = None

class AdminAnalytics(BaseModel):
    total_students: int
    total_drives: int
    total_matches: int
    total_interviews: int
    matches_by_branch: List[Dict[str, Any]]
