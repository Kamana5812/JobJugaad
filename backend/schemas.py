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
    student_id: int | None = None
    company_id: int | None = None
    college_id: int
    role: Literal["student", "recruiter"] = "student"
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

# Phase 2 matching inputs and outputs: weights are explicit assumptions.
from datetime import datetime
from pydantic import model_validator

class CompanyInput(InputModel):
    name: str = Field(min_length=1, max_length=160)
    industry: str = Field(min_length=1, max_length=100)

class CompanyResponse(CompanyInput):
    id: int
    college_id: int
    recruiter_user_id: int

class RecruiterSignupRequest(LoginRequest):
    company: CompanyInput

class RequiredSkill(InputModel):
    skill_name: str = Field(min_length=1, max_length=80)
    min_proficiency: float = Field(ge=1, le=100, allow_inf_nan=False)

    @field_validator("skill_name")
    @classmethod
    def normalize(cls, value):
        return " ".join(value.lower().split())

class MatchingWeights(InputModel):
    skills: int = Field(default=40, ge=0, le=100, strict=True)
    projects: int = Field(default=20, ge=0, le=100, strict=True)
    academics: int = Field(default=20, ge=0, le=100, strict=True)
    assessments: int = Field(default=15, ge=0, le=100, strict=True)
    certifications: int = Field(default=5, ge=0, le=100, strict=True)

    @model_validator(mode="after")
    def total(self):
        if sum(self.model_dump().values()) != 100:
            raise ValueError("Matching weights must sum to 100.")
        return self

class JobInput(InputModel):
    title: str = Field(min_length=1, max_length=160)
    ctc: float = Field(gt=0, le=1000, allow_inf_nan=False)
    min_cgpa: float = Field(ge=0, le=10, allow_inf_nan=False)
    max_backlogs: int = Field(default=0, ge=0, le=100, strict=True)
    eligible_branches: list[str] = Field(min_length=1, max_length=30)
    required_skills: list[RequiredSkill] = Field(min_length=1, max_length=20)
    weights: MatchingWeights = Field(default_factory=MatchingWeights)
    min_match_score: Score = 60
    assessment_benchmark: Score = 60

    @field_validator("eligible_branches")
    @classmethod
    def branches(cls, value):
        result = [" ".join(b.strip().upper().split()) for b in value]
        if any(not b or len(b) > 80 for b in result) or len(set(result)) != len(result):
            raise ValueError("Use unique, nonempty branch names of at most 80 characters.")
        return result

    @field_validator("required_skills")
    @classmethod
    def unique_requirements(cls, value):
        if len({item.skill_name for item in value}) != len(value):
            raise ValueError("Each required skill should appear only once.")
        return value

class JobResponse(JobInput):
    id: int
    college_id: int
    company_id: int
    created_at: datetime

class SkillGapResponse(BaseModel):
    skill_name: str
    proficiency: float
    required: float
    shortfall: float
    status: Literal["on-track", "gap", "critical"]
    explanation: str
    next_step: str

class MatchCalculation(BaseModel):
    match_score: float
    factor_breakdown: list[FactorResponse]
    missing_requirements: list[str]
    skill_gaps: list[SkillGapResponse]
    eligible: bool
    explanation: str
    next_step: str
    methodology: str

class OverrideInput(InputModel):
    action: Literal["promote", "reject"]
    reason: str = Field(min_length=10, max_length=1000)

class OverrideResponse(BaseModel):
    id: int
    match_id: int
    recruiter_user_id: int
    action: Literal["promote", "reject"]
    reason: str
    previous_action: str | None
    created_at: datetime
    evidence_at_action: MatchCalculation

class CandidateResponse(MatchCalculation):
    id: int
    job_id: int
    student_id: int
    student_name: str
    branch: str
    calculated_at: datetime
    override_action: Literal["promote", "reject"] | None
    shortlist_status: Literal["shortlisted", "excluded"]
    audit: list[OverrideResponse]

class MatchSummary(BaseModel):
    job_id: int
    total: int
    shortlisted: int
    excluded: int
    overridden: int

class MatchResults(MatchSummary):
    candidates: list[CandidateResponse]
    offset: int
    limit: int
