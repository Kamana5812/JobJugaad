"""Phase 1 models; composite foreign keys enforce tenant consistency."""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class TenantRow:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    college_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

class User(TenantRow, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("college_id", "email"), UniqueConstraint("id", "college_id"),
        CheckConstraint("college_id > 0"), CheckConstraint("role IN ('student','recruiter','admin')"))

class Student(TenantRow, Base):
    __tablename__ = "students"
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    branch: Mapped[str] = mapped_column(String(80), default="Not specified")
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    backlog_count: Mapped[int] = mapped_column(Integer, default=0)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    aptitude_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    interview_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    readiness_score: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("id", "college_id"),
        ForeignKeyConstraint(["user_id", "college_id"], ["users.id", "users.college_id"]),
        CheckConstraint("cgpa IS NULL OR cgpa BETWEEN 0 AND 10"), CheckConstraint("backlog_count >= 0"),
        CheckConstraint("aptitude_score IS NULL OR aptitude_score BETWEEN 0 AND 100"),
        CheckConstraint("communication_score IS NULL OR communication_score BETWEEN 0 AND 100"),
        CheckConstraint("interview_score IS NULL OR interview_score BETWEEN 0 AND 100"),
        CheckConstraint("readiness_score BETWEEN 0 AND 100"))

class StudentSkill(TenantRow, Base):
    __tablename__ = "student_skills"
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(80), nullable=False)
    proficiency: Mapped[float] = mapped_column(Float, nullable=False)
    __table_args__ = (ForeignKeyConstraint(["student_id", "college_id"], ["students.id", "students.college_id"]),
        UniqueConstraint("student_id", "college_id", "skill_name"), CheckConstraint("proficiency BETWEEN 0 AND 100"))

class Project(TenantRow, Base):
    __tablename__ = "projects"
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (ForeignKeyConstraint(["student_id", "college_id"], ["students.id", "students.college_id"]),)

class Certification(TenantRow, Base):
    __tablename__ = "certifications"
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (ForeignKeyConstraint(["student_id", "college_id"], ["students.id", "students.college_id"]),)

# Phase 2: JSON stores explicit evidence snapshots, never calibrated confidence.
from sqlalchemy import JSON, Boolean, Numeric

class Company(TenantRow, Base):
    __tablename__ = "companies"
    recruiter_user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint("id", "college_id"),
        ForeignKeyConstraint(["recruiter_user_id", "college_id"], ["users.id", "users.college_id"]),)

class Job(TenantRow, Base):
    __tablename__ = "jobs"
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    ctc: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # INR lakh per annum
    min_cgpa: Mapped[float] = mapped_column(Float, nullable=False)
    max_backlogs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eligible_branches: Mapped[list] = mapped_column(JSON, nullable=False)
    required_skills: Mapped[list] = mapped_column(JSON, nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    min_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=60)
    assessment_benchmark: Mapped[float] = mapped_column(Float, nullable=False, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("id", "college_id"),
        ForeignKeyConstraint(["company_id", "college_id"], ["companies.id", "companies.college_id"]),
        CheckConstraint("ctc > 0"), CheckConstraint("min_cgpa BETWEEN 0 AND 10"),
        CheckConstraint("max_backlogs >= 0"), CheckConstraint("min_match_score BETWEEN 0 AND 100"),
        CheckConstraint("assessment_benchmark BETWEEN 0 AND 100"))

class Match(TenantRow, Base):
    __tablename__ = "matches"
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    factor_breakdown: Mapped[list] = mapped_column(JSON, nullable=False)
    missing_requirements: Mapped[list] = mapped_column(JSON, nullable=False)
    skill_gaps: Mapped[list] = mapped_column(JSON, nullable=False)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    next_step: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[str] = mapped_column(Text, nullable=False)
    override_action: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("id", "college_id"), UniqueConstraint("job_id", "student_id", "college_id"),
        ForeignKeyConstraint(["job_id", "college_id"], ["jobs.id", "jobs.college_id"]),
        ForeignKeyConstraint(["student_id", "college_id"], ["students.id", "students.college_id"]),
        CheckConstraint("match_score BETWEEN 0 AND 100"),
        CheckConstraint("override_action IS NULL OR override_action IN ('promote','reject')"))

class MatchOverride(TenantRow, Base):
    __tablename__ = "match_overrides"
    match_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    recruiter_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    previous_action: Mapped[str | None] = mapped_column(String(20), nullable=True)
    score_at_action: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_at_action: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (ForeignKeyConstraint(["match_id", "college_id"], ["matches.id", "matches.college_id"]),
        ForeignKeyConstraint(["recruiter_user_id", "college_id"], ["users.id", "users.college_id"]),
        CheckConstraint("action IN ('promote','reject')"))
