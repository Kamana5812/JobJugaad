"""Validated contracts; every readiness response includes factors and explanation."""
import re
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Score = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Name = Annotated[str, Field(min_length=1, max_length=100)]

class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["jobjugaad-api"] = "jobjugaad-api"
    database: Literal["connected", "not_configured"]

class LoginRequest(InputModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=72)
    college_id: Literal[1, 2]

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("password")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72 or "\x00" in value:
            raise ValueError("Password must be at most 72 UTF-8 bytes with no null characters.")
        return value

class SignupRequest(LoginRequest):
    name: Name

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value

class UserResponse(BaseModel):
    user_id: int
    student_id: int
    college_id: int
    role: Literal["student"] = "student"
    email: str
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse

class SkillInput(InputModel):
    skill_name: str = Field(min_length=1, max_length=80)
    proficiency: Score

    @field_validator("skill_name")
    @classmethod
    def normalize(cls, value):
        return value.lower()

class EvidenceInput(InputModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=3000)

class ProfileUpdate(InputModel):
    name: Name
    branch: str = Field(min_length=1, max_length=80)
    cgpa: float | None = Field(default=None, ge=0, le=10, allow_inf_nan=False)
    backlog_count: int = Field(default=0, ge=0, le=100, strict=True)
    aptitude_score: Score | None = None
    communication_score: Score | None = None
    interview_score: Score | None = None
    skills: list[SkillInput] = Field(default_factory=list, max_length=30)
    projects: list[EvidenceInput] = Field(default_factory=list, max_length=20)
    certifications: list[EvidenceInput] = Field(default_factory=list, max_length=20)

    @field_validator("skills")
    @classmethod
    def unique_skills(cls, value):
        if len({item.skill_name for item in value}) != len(value):
            raise ValueError("Each skill should appear only once.")
        return value

class FactorResponse(BaseModel):
    key: str
    label: str
    value: float
    weight: int
    contribution: float
    evidence: str
    missing: bool

class ReadinessResponse(BaseModel):
    score: int
    raw_score: float
    band: Literal["Not Ready", "Developing", "Ready", "Highly Employable"]
    breakdown: list[FactorResponse]
    explanation: str
    methodology: str
    next_step: str

class ProfileResponse(ProfileUpdate):
    id: int
    college_id: int
    user_id: int
    resume_text: str | None
    readiness: ReadinessResponse

class ResumeResponse(BaseModel):
    detail: str
    extracted_characters: int
    profile: ProfileResponse
