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

# Phase 3: proposals are separate from confirmed bookings; all tenant rows get RLS.
class Schedule(TenantRow, Base):
    __tablename__ = "schedules"
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    requested_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    venue: Mapped[str] = mapped_column(String(100), nullable=False)
    panel_id: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    conflicts: Mapped[list] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    reschedule_interview_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("id", "college_id"),
        ForeignKeyConstraint(["job_id","college_id"], ["jobs.id","jobs.college_id"]),
        ForeignKeyConstraint(["student_id","college_id"], ["students.id","students.college_id"]),
        ForeignKeyConstraint(["created_by","college_id"], ["users.id","users.college_id"]),
        ForeignKeyConstraint(["reviewed_by","college_id"], ["users.id","users.college_id"]),
        ForeignKeyConstraint(["reschedule_interview_id","college_id"], ["interviews.id","interviews.college_id"],
            use_alter=True, name="fk_schedule_source_interview_tenant"),
        CheckConstraint("end_time > scheduled_time"), CheckConstraint("status IN ('pending','scheduled','rejected')"))

class Interview(TenantRow, Base):
    __tablename__ = "interviews"
    schedule_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    venue: Mapped[str] = mapped_column(String(100), nullable=False)
    panel_id: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    seed_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    __table_args__ = (UniqueConstraint("id","college_id"), UniqueConstraint("college_id","seed_key"),
        ForeignKeyConstraint(["schedule_id","college_id"], ["schedules.id","schedules.college_id"]),
        ForeignKeyConstraint(["job_id","college_id"], ["jobs.id","jobs.college_id"]),
        ForeignKeyConstraint(["student_id","college_id"], ["students.id","students.college_id"]),
        CheckConstraint("end_time > scheduled_time"),
        CheckConstraint("status IN ('scheduled','completed','selected','rejected','cancelled')"))

class ScheduleEvent(TenantRow, Base):
    __tablename__ = "schedule_events"
    schedule_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interview_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        ForeignKeyConstraint(["schedule_id","college_id"], ["schedules.id","schedules.college_id"]),
        ForeignKeyConstraint(["interview_id","college_id"], ["interviews.id","interviews.college_id"]),
        ForeignKeyConstraint(["actor_user_id","college_id"], ["users.id","users.college_id"]),)

class RiskPrediction(TenantRow, Base):
    __tablename__ = "risk_predictions"
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    support_priority: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # Count of triggered rules /3, NOT probability.
    contributing_factors: Mapped[list] = mapped_column(JSON, nullable=False)
    recommendation: Mapped[list] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    flagged: Mapped[bool] = mapped_column(Boolean, nullable=False)
    assessable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    review_status: Mapped[str] = mapped_column(String(20), default="active")
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (UniqueConstraint("id","college_id"), UniqueConstraint("college_id","student_id","job_id"),
        ForeignKeyConstraint(["student_id","college_id"], ["students.id","students.college_id"]),
        ForeignKeyConstraint(["job_id","college_id"], ["jobs.id","jobs.college_id"]),
        CheckConstraint("score BETWEEN 0 AND 3"), CheckConstraint("support_priority IN ('low','high')"),
        CheckConstraint("review_status IN ('active','reviewed','dismissed')"))

class SupportReview(TenantRow, Base):
    __tablename__ = "support_reviews"
    prediction_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        ForeignKeyConstraint(["prediction_id","college_id"], ["risk_predictions.id","risk_predictions.college_id"]),
        ForeignKeyConstraint(["actor_user_id","college_id"], ["users.id","users.college_id"]),
        CheckConstraint("action IN ('active','reviewed','dismissed')"),)

# Phase 4: distinct lifecycle stages, recipient-scoped feeds and retained change history.
class Offer(TenantRow, Base):
    __tablename__ = "offers"
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    interview_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ctc: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    offer_letter_status: Mapped[str] = mapped_column(String(24), default="draft")
    documents_status: Mapped[str] = mapped_column(String(24), default="pending")
    verification_status: Mapped[str] = mapped_column(String(24), default="pending")
    acceptance_status: Mapped[str] = mapped_column(String(24), default="pending")
    joining_status: Mapped[str] = mapped_column(String(24), default="pending")
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seed_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("id","college_id"), UniqueConstraint("college_id","student_id","job_id"),
        UniqueConstraint("college_id","seed_key"),
        ForeignKeyConstraint(["student_id","college_id"],["students.id","students.college_id"]),
        ForeignKeyConstraint(["job_id","college_id"],["jobs.id","jobs.college_id"]),
        ForeignKeyConstraint(["interview_id","college_id"],["interviews.id","interviews.college_id"]),
        CheckConstraint("ctc > 0"),
        CheckConstraint("offer_letter_status IN ('draft','issued','withdrawn')"),
        CheckConstraint("documents_status IN ('pending','submitted','changes_requested')"),
        CheckConstraint("verification_status IN ('pending','verified','rejected')"),
        CheckConstraint("acceptance_status IN ('pending','accepted','declined')"),
        CheckConstraint("joining_status IN ('pending','joined','not_joined')"),
        CheckConstraint("verification_status != 'verified' OR documents_status = 'submitted'"),
        CheckConstraint("joining_status != 'joined' OR (offer_letter_status = 'issued' AND acceptance_status = 'accepted' AND verification_status = 'verified')"))

class OfferEvent(TenantRow, Base):
    __tablename__ = "offer_events"
    offer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        ForeignKeyConstraint(["offer_id","college_id"],["offers.id","offers.college_id"]),
        ForeignKeyConstraint(["actor_user_id","college_id"],["users.id","users.college_id"]),)

class Notification(TenantRow, Base):
    __tablename__ = "notifications"
    recipient_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_key: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    target_path: Mapped[str] = mapped_column(String(160), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("college_id","recipient_user_id","event_key"),
        ForeignKeyConstraint(["recipient_user_id","college_id"],["users.id","users.college_id"]),)


class PlacementModelProfile(TenantRow, Base):
    """Optional, student-supplied academic inputs; never populated from synthetic seeds."""
    __tablename__ = "placement_model_profiles"
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("student_id", "college_id"),
        ForeignKeyConstraint(["student_id", "college_id"], ["students.id", "students.college_id"]),)
