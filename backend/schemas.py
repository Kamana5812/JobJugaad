from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict

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
