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
