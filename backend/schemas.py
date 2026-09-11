from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    branch: str
    cgpa: float = Field(..., gt=0, lt=11)
    role: str = "student"  # "student" or "recruiter"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class StudentSkillSchema(BaseModel):
    skill_name: str
    proficiency: int

    class Config:
        orm_mode = True

class ProjectSchema(BaseModel):
    title: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class CertificationSchema(BaseModel):
    title: str
    institution: Optional[str] = None
    year: Optional[int] = None

    class Config:
        orm_mode = True

class StudentOut(BaseModel):
    name: str
    branch: str
    cgpa: float
    backlog_count: int
    resume_text: Optional[str] = None
    aptitude_score: float
    communication_score: float
    interview_score: float
    readiness_score: float
    skills: List[StudentSkillSchema] = []
    projects: List[ProjectSchema] = []
    certifications: List[CertificationSchema] = []

    class Config:
        orm_mode = True

class ReadinessOut(BaseModel):
    score: float
    band: str
    explanation: str
    breakdown: dict

    class Config:
        orm_mode = True

# Recruiter & Job schemas
class CompanySchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class CompanyCreate(BaseModel):
    name: str

class JobCreate(BaseModel):
    title: str
    ctc: float
    min_cgpa: float
    eligible_branches: str  # comma‑separated list
    required_skills: str  # comma‑separated list

class JobOut(BaseModel):
    id: int
    title: str
    ctc: float
    min_cgpa: float
    eligible_branches: str
    required_skills: str
    company: CompanySchema

    class Config:
        orm_mode = True

class MatchOut(BaseModel):
    student_id: int
    name: str
    score: float
    breakdown: dict

    class Config:
        orm_mode = True
