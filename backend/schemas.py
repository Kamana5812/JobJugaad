from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    branch: str
    cgpa: float

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    college_id: Optional[str] = None
    user_id: Optional[int] = None

# --- Student Profile ---
class Skill(BaseModel):
    id: int
    skill_name: str
    proficiency: int
    class Config:
        from_attributes = True

class Project(BaseModel):
    id: int
    title: str
    description: str
    class Config:
        from_attributes = True

class Certification(BaseModel):
    id: int
    title: str
    description: str
    class Config:
        from_attributes = True

class StudentProfile(BaseModel):
    id: int
    user_id: int
    name: str
    branch: str
    cgpa: float
    backlog_count: int
    resume_text: Optional[str] = None
    readiness_score: float
    skills: List[Skill] = []
    projects: List[Project] = []
    certifications: List[Certification] = []

    class Config:
        from_attributes = True

# --- Readiness Output ---
class ReadinessResponse(BaseModel):
    score: float
    band: str
    breakdown: Dict[str, float]
    explanation: str

# --- Recruiter & Jobs ---
class CompanyCreate(BaseModel):
    name: str
    industry: str

class CompanyProfile(BaseModel):
    id: int
    recruiter_user_id: int
    name: str
    industry: str
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    title: str
    ctc: float
    min_cgpa: float
    eligible_branches: List[str]
    required_skills: List[str]

class JobProfile(BaseModel):
    id: int
    company_id: int
    title: str
    ctc: float
    min_cgpa: float
    eligible_branches: List[str]
    required_skills: List[str]
    created_at: datetime
    class Config:
        from_attributes = True

class MatchResult(BaseModel):
    id: int
    job_id: int
    student_id: int
    student_name: str
    match_score: float
    factor_breakdown: Dict[str, Any]
    missing_requirements: List[str]
    explanation: str
    class Config:
        from_attributes = True
