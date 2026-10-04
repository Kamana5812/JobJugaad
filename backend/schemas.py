"""Validated contracts; every readiness response includes factors and explanation."""
import re
from uuid import UUID
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Score = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
Name = Annotated[str, Field(min_length=1, max_length=100)]

class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class AssessmentInput(InputModel):
    student_id: int = Field(gt=0)
    kind: Literal['aptitude', 'communication', 'interview', 'skill']
    skill_name: str | None = Field(None, min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=160)
    source: str = Field(min_length=1, max_length=160)
    reference: str = Field(min_length=1, max_length=200)
    assessed_on: str = Field(min_length=10, max_length=40)
    score: float = Field(ge=0, le=100000, allow_inf_nan=False)
    maximum: float = Field(gt=0, le=100000, allow_inf_nan=False)
    reason: str = Field(min_length=10, max_length=1000)

class AssessmentWithdrawal(InputModel):
    reason: str = Field(min_length=10, max_length=1000)

class AssessmentResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    kind: str
    skill_name: str | None
    title: str
    source: str
    reference: str
    assessed_on: str
    score: float
    maximum: float
    normalized_score: float
    explanation: str
    recorded_by: int
    created_at: str
    reason: str
    withdrawn_at: str | None
    withdrawn_by: int | None
    withdrawal_reason: str | None

class AssessmentList(BaseModel):
    items: list[AssessmentResponse]
    total: int
    offset: int
    limit: int
    methodology: str = 'Staff-recorded evidence from external assessments; no independent exam authentication. Readiness, matching and support still use self-reported profile inputs.'

class IsolationTableResponse(BaseModel):
    table: str
    college_id: bool
    enabled: bool
    forced: bool
    policy: str | None
    read_write_scoped: bool
    status: Literal["verified", "failed"]

class IsolationResponse(BaseModel):
    status: Literal["verified", "failed"]
    runtime_role_restricted: bool
    tables: list[IsolationTableResponse]

class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["jobjugaad-api"] = "jobjugaad-api"
    database: Literal["connected", "not_configured"]
    isolation: IsolationResponse
    placement_model: Literal["ready", "unavailable", "not_loaded"] = "not_loaded"
    btech_model: Literal["ready", "unavailable", "not_loaded"] = "not_loaded"

class LoginRequest(InputModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=72)
    college_id: int = Field(ge=1, strict=True)

    @field_validator("college_id")
    @classmethod
    def registered_college(cls, value):
        from colleges import valid_college
        if not valid_college(value):
            raise ValueError("Choose a college from the registered directory.")
        return value

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

class PasswordResetRequest(InputModel):
    email: str = Field(min_length=3, max_length=254)
    college_id: int = Field(ge=1, strict=True)

    @field_validator('email')
    @classmethod
    def email_address(cls, value):
        return LoginRequest.valid_email(value)

    @field_validator('college_id')
    @classmethod
    def college(cls, value):
        return LoginRequest.registered_college(value)

class PasswordResetInput(InputModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=False)
    college_id: int = Field(ge=1, strict=True)
    token: str = Field(pattern=r'^[A-Za-z0-9_-]{43}$')
    password: str = Field(min_length=10, max_length=72)

    @field_validator('college_id')
    @classmethod
    def college(cls, value):
        return LoginRequest.registered_college(value)

    @field_validator('password')
    @classmethod
    def password_bytes(cls, value):
        return LoginRequest.password_bytes(value)

class UserResponse(BaseModel):
    email_verified: bool = False
    access_status: Literal["unverified", "pending", "approved", "rejected", "legacy_demo"] = "unverified"
    is_demo: bool = False
    college_name: str
    user_id: int
    student_id: int | None = None
    company_id: int | None = None
    college_id: int
    role: Literal["student", "recruiter", "admin"] = "student"
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

# Phase 3 contracts: support numbers are rule counts accompanied by evidence.
from pydantic import AwareDatetime

class AdminAccountConfig(InputModel):
    email: str
    college_id: int = Field(ge=1, strict=True)

    @field_validator("college_id")
    @classmethod
    def registered_college(cls, value):
        from colleges import valid_college
        if not valid_college(value):
            raise ValueError("Unknown college in administrator configuration.")
        return value


class ScheduleInput(InputModel):
    job_id: int = Field(gt=0)
    student_id: int = Field(gt=0)
    scheduled_time: AwareDatetime
    duration_minutes: int = Field(default=30, ge=5, le=240, strict=True)
    venue: str = Field(min_length=1, max_length=100)
    panel_id: str = Field(min_length=1, max_length=80)
    reschedule_interview_id: int | None = Field(default=None, gt=0)
    round_number: int = Field(default=1, ge=1, le=20, strict=True)
    round_name: str = Field(default="Interview", min_length=1, max_length=80)

    @field_validator("venue", "panel_id")
    @classmethod
    def normalize_resource(cls, value):
        return " ".join(value.lower().split())

class ConflictResponse(BaseModel):
    interview_id: int
    job_id: int
    student_id: int
    scheduled_time: datetime
    end_time: datetime
    kinds: list[Literal["student", "venue", "panel", "overlapping_drive"]]
    explanation: str

class CalendarConflictResponse(BaseModel):
    constraint_id: int | None = None
    kind: str
    explanation: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None

class SlotProposal(BaseModel):
    requested_time: datetime
    proposed_time: datetime | None
    proposed_end_time: datetime | None
    conflicts: list[ConflictResponse]
    calendar_conflicts: list[CalendarConflictResponse] = Field(default_factory=list)
    explanation: str
    requires_approval: Literal[True] = True
    methodology: str

class ScheduleResponse(BaseModel):
    id: int
    college_id: int
    job_id: int
    student_id: int
    requested_time: datetime
    scheduled_time: datetime
    end_time: datetime
    venue: str
    panel_id: str
    status: str
    conflicts: list[ConflictResponse]
    calendar_conflicts: list[CalendarConflictResponse] = Field(default_factory=list)
    round_number: int = 1
    round_name: str = "Interview"
    explanation: str
    reschedule_interview_id: int | None
    version: int
    review_reason: str | None
    reviewed_by: int | None
    created_at: datetime

class InterviewResponse(BaseModel):
    id: int
    college_id: int
    schedule_id: int | None
    job_id: int
    student_id: int
    scheduled_time: datetime
    end_time: datetime
    venue: str
    panel_id: str
    status: str
    seed_key: str | None
    round_number: int = 1
    round_name: str = "Interview"

class AuditEventResponse(BaseModel):
    id: int
    actor_user_id: int
    action: str
    reason: str
    snapshot: dict
    created_at: datetime

class ScheduleReviewInput(InputModel):
    action: Literal["approve","reject"]
    version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=10,max_length=1000)

class ScheduleRecheckInput(InputModel):
    version: int = Field(ge=1, strict=True)

class InterviewStatusInput(InputModel):
    status: Literal["completed","selected","rejected","cancelled"]
    reason: str = Field(min_length=10,max_length=1000)

class NamedOption(BaseModel):
    id: int
    name: str

class BookingConflict(BaseModel):
    interview_id: int
    other_interview_id: int
    kinds: list[str]
    explanation: str

class CalendarBookingAlert(BaseModel):
    interview_id: int
    explanation: str
    kinds: list[str]

class SchedulingBoard(BaseModel):
    applicants: list["SchedulingApplicant"] = Field(default_factory=list)
    jobs: list[NamedOption]
    students: list[NamedOption]
    interviews: list[InterviewResponse]
    proposals: list[ScheduleResponse]
    conflicts: list[BookingConflict]
    calendar_alerts: list[CalendarBookingAlert] = Field(default_factory=list)
    audit: list[AuditEventResponse]

class CalendarSettingsResponse(BaseModel):
    college_id: int
    version: int = 0
    enabled: bool = False
    timezone: str = "Asia/Kolkata"
    weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])
    day_start: str = "09:00"
    day_end: str = "17:00"
    require_student_availability: bool = False
    require_panel_availability: bool = False

class CalendarSettingsInput(InputModel):
    version: int = Field(ge=0, strict=True)
    enabled: bool
    timezone: str = Field(min_length=1, max_length=80)
    weekdays: list[Annotated[int, Field(ge=0, le=6, strict=True)]] = Field(min_length=1, max_length=7)
    day_start: str
    day_end: str
    require_student_availability: bool = False
    require_panel_availability: bool = False
    reason: str = Field(min_length=10, max_length=1000)

    @field_validator("timezone")
    @classmethod
    def recognized_timezone(cls, value):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Choose an available IANA timezone such as Asia/Kolkata.") from None
        return value

    @field_validator("weekdays")
    @classmethod
    def unique_weekdays(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Choose each weekday only once; Monday is 0.")
        return sorted(value)

    @field_validator("day_start", "day_end")
    @classmethod
    def clock_time(cls, value):
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise ValueError("Use a 24-hour HH:MM time.")
        return value

    @model_validator(mode="after")
    def same_day_hours(self):
        if self.day_start >= self.day_end:
            raise ValueError("Campus closing time must be after opening time on the same local day.")
        return self

class CalendarConstraintInput(InputModel):
    kind: Literal["available", "unavailable", "exam"]
    scope: Literal["student", "panel", "campus", "branch"]
    student_id: int | None = Field(default=None, gt=0, strict=True)
    resource_name: str | None = Field(default=None, min_length=1, max_length=80)
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    label: str = Field(min_length=3, max_length=160)
    reason: str = Field(min_length=10, max_length=1000)

    @model_validator(mode="after")
    def valid_scope(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("The end must be after the start.")
        if self.scope in ("student", "panel") and self.kind == "exam":
            raise ValueError("Exams must have campus or branch scope.")
        if self.scope in ("campus", "branch") and self.kind != "exam":
            raise ValueError("Campus and branch constraints must be exam blocks.")
        if self.scope == "student":
            if self.student_id is None or self.resource_name is not None:
                raise ValueError("Student scope needs a student ID only.")
        elif self.scope in ("panel", "branch"):
            if self.student_id is not None or not self.resource_name or not self.resource_name.strip():
                raise ValueError("Panel or branch scope needs its resource name only.")
            normalized = " ".join(self.resource_name.split())
            self.resource_name = normalized.upper() if self.scope == "branch" else normalized.lower()
        elif self.student_id is not None or self.resource_name is not None:
            raise ValueError("Campus scope cannot specify a student or resource.")
        return self

class StudentAvailabilityInput(InputModel):
    kind: Literal["available", "unavailable"]
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    label: str = Field(min_length=3, max_length=160)

    @model_validator(mode="after")
    def valid_interval(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("The end must be after the start.")
        return self

class CalendarCancelInput(InputModel):
    version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=10, max_length=1000)

class CalendarConstraintResponse(BaseModel):
    id: int
    college_id: int
    kind: Literal["available", "unavailable", "exam"]
    scope: Literal["student", "panel", "campus", "branch"]
    student_id: int | None
    resource_name: str | None
    starts_at: datetime
    ends_at: datetime
    label: str
    status: Literal["active", "cancelled"]
    version: int

class CalendarConstraintList(BaseModel):
    items: list[CalendarConstraintResponse]
    total: int
    offset: int
    limit: int

class ConversionRow(BaseModel):
    name: str
    total_students: int
    shortlisted_students: int
    conversion_percent: float | None

class AnalyticsResponse(BaseModel):
    accepted_students: int = 0
    joined_students: int = 0
    offer_count: int = 0
    synthetic_offer_count: int = 0
    accepted_ctc_min_lpa: float | None = None
    accepted_ctc_max_lpa: float | None = None
    accepted_ctc_mean_lpa: float | None = None
    students: int
    recruiters: int
    drives: int
    placement_percent: float | None
    placement_explanation: str
    branch_conversion: list[ConversionRow]
    skill_conversion: list[ConversionRow]
    ctc_min_lpa: float | None
    ctc_max_lpa: float | None
    ctc_mean_lpa: float | None
    methodology: str
    generated_at: datetime

class PostSelectionDrive(BaseModel):
    id: int
    title: str

class PostSelectionCohort(BaseModel):
    selected_pairs: int
    distinct_students: int
    offers: int
    without_offer: int
    synthetic_pairs: int
    recorded_pairs: int
    excluded_pairs: int

class PostSelectionStage(BaseModel):
    key: Literal["selected", "issued", "accepted", "verified", "joined"]
    label: str
    count: int
    distinct_students: int
    previous_count: int | None
    conversion_percent: float | None
    not_reached_from_previous: int
    pending_from_previous: int
    closed_from_previous: int
    explanation: str

class PostSelectionMilestone(BaseModel):
    key: Literal["issued", "accepted", "verified", "joined", "verified_without_acceptance"]
    label: str
    count: int
    distinct_students: int
    explanation: str

class PostSelectionClosure(BaseModel):
    key: Literal["withdrawn", "declined", "not_joined"]
    label: str
    count: int
    distinct_students: int
    missing_reason_count: int
    explanation: str

class PostSelectionReason(BaseModel):
    closure: Literal["withdrawn", "declined", "not_joined"]
    reason: str
    reason_source: Literal["recorded_action", "synthetic_import", "missing"]
    count: int
    synthetic_count: int
    recorded_count: int

class PostSelectionDataQuality(BaseModel):
    offers_without_history: int
    invalid_offer_history_events: int
    invalid_selection_history_events: int
    withdrawn_without_issuance_evidence: int
    accepted_without_issuance_evidence: int
    selection_from_linked_offer: int
    selection_from_history: int
    offers_with_mismatched_interview: int
    historical_selection_no_current_selection: int

class PostSelectionAnalytics(BaseModel):
    scope: Literal["recorded", "synthetic", "all"]
    college_id: int
    job_id: int | None
    archive_demo: bool
    scope_explanation: str
    drives: list[PostSelectionDrive]
    cohort: PostSelectionCohort
    stages: list[PostSelectionStage]
    milestones: list[PostSelectionMilestone]
    closures: list[PostSelectionClosure]
    reasons: list[PostSelectionReason]
    reason_total: int
    offset: int
    limit: int
    data_quality: PostSelectionDataQuality
    methodology: str
    limitations: list[str]
    generated_at: datetime

class SupportFactor(BaseModel):
    key: str
    label: str
    value: float | None
    threshold: str
    triggered: bool
    contribution: Literal[0,1]
    explanation: str

class Intervention(BaseModel):
    category: str
    action: str

class SupportCalculation(BaseModel):
    score: int
    score_label: Literal["Support indicators met /3"] = "Support indicators met /3"
    support_priority: Literal["low","high"]
    flagged: bool
    assessable: bool
    contributing_factors: list[SupportFactor]
    recommendation: list[Intervention]
    explanation: str
    methodology: str

class SupportResponse(SupportCalculation):
    id: int
    job_id: int
    student_id: int
    student_name: str
    review_status: Literal["active","reviewed","dismissed"]
    evaluated_at: datetime
    audit: list[AuditEventResponse]

class SupportReport(BaseModel):
    job_id: int
    total_evaluated: int
    flagged_count: int
    active_count: int
    unknown_interview_score_count: int
    students: list[SupportResponse]
    methodology: str

class SupportRunInput(InputModel):
    job_id: int = Field(gt=0)

class SupportReviewInput(InputModel):
    action: Literal["active","reviewed","dismissed"]
    reason: str = Field(min_length=10,max_length=1000)

# Phase 4 lifecycle contracts. These are recorded statuses, not document verification software.
class OfferCreate(InputModel):
    interview_id: int = Field(gt=0)
    ctc: float | None = Field(default=None, gt=0, le=10000, allow_inf_nan=False)
    reason: str = Field(min_length=10, max_length=1000)

class OfferAdminUpdate(InputModel):
    stage: Literal["offer_letter_status","documents_status","verification_status","joining_status"]
    value: str = Field(min_length=1, max_length=24)
    version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=10, max_length=1000)

class OfferStudentAction(InputModel):
    action: Literal["submit_documents","accept","decline"]
    version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=10, max_length=1000)

class OfferAuditResponse(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    reason: str
    snapshot: dict
    created_at: datetime

class OfferResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    job_id: int
    job_title: str
    company_name: str
    interview_id: int
    ctc: float
    offer_letter_status: Literal["draft","issued","withdrawn"]
    documents_status: Literal["pending","submitted","changes_requested"]
    verification_status: Literal["pending","verified","rejected"]
    acceptance_status: Literal["pending","accepted","declined"]
    joining_status: Literal["pending","joined","not_joined"]
    version: int
    is_synthetic: bool
    created_at: datetime
    updated_at: datetime
    next_steps: list[str]
    audit: list[OfferAuditResponse]
    methodology: str

class OfferList(BaseModel):
    offers: list[OfferResponse]
    total: int
    offset: int
    limit: int

class OfferCandidate(BaseModel):
    interview_id: int
    student_id: int
    student_name: str
    job_title: str
    ctc: float

class OfferCandidateList(BaseModel):
    candidates: list[OfferCandidate]
    total: int
    offset: int
    limit: int


class OfferDocumentUpload(InputModel):
    # Multipart values arrive as strings; JSON review still uses strict version integers.
    version: int = Field(ge=1)
    label: str = Field(min_length=3, max_length=160)
    reason: str = Field(min_length=10, max_length=1000)
    idempotency_key: UUID
    replaces_document_id: int | None = Field(default=None, gt=0)

    @field_validator("label", "reason")
    @classmethod
    def plain_text_without_null(cls, value):
        if "\x00" in value:
            raise ValueError("Use plain text without null characters.")
        return value


class OfferDocumentReview(InputModel):
    version: int = Field(ge=1, strict=True)
    review_status: Literal["verified", "rejected"]
    reason: str = Field(min_length=10, max_length=1000)

    @field_validator("reason")
    @classmethod
    def plain_text_without_null(cls, value):
        if "\x00" in value:
            raise ValueError("Use plain text without null characters.")
        return value


class OfferDocumentResponse(BaseModel):
    id: int
    offer_id: int
    kind: Literal["offer_letter", "supporting_document"]
    label: str
    original_filename: str
    size_bytes: int
    sha256: str
    page_count: int
    uploaded_by: int
    uploaded_at: datetime
    uploaded_offer_version: int
    is_active: bool
    supersedes_document_id: int | None
    review_status: Literal["pending", "verified", "rejected"]
    reviewed_by: int | None
    reviewed_at: datetime | None
    review_reason: str | None


class OfferDocumentLimits(BaseModel):
    max_bytes: int
    max_pages: int
    max_files: int
    max_offer_bytes: int
    stored_files: int
    stored_bytes: int


class OfferDocumentList(BaseModel):
    items: list[OfferDocumentResponse]
    total: int
    offset: int
    limit: int
    offer_version: int
    limits: OfferDocumentLimits
    explanation: str


class OfferDocumentMutation(BaseModel):
    offer: OfferResponse
    document: OfferDocumentResponse


class OfferDocumentEventResponse(BaseModel):
    id: int
    actor_user_id: int
    action: str
    reason: str
    created_at: datetime


class OfferDocumentEventList(BaseModel):
    items: list[OfferDocumentEventResponse]
    total: int
    offset: int
    limit: int
    explanation: str

class NotificationResponse(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    target_path: str
    read_at: datetime | None
    created_at: datetime
    delivery: Literal["simulated_in_app", "in_app"] = "simulated_in_app"

class NotificationFeed(BaseModel):
    notifications: list[NotificationResponse]
    unread_count: int
    total: int
    offset: int
    limit: int
    explanation: str = "Simulated in-app records only. No email or SMS is sent."


class PlacementModelInput(InputModel):
    # Missing evidence stays missing. No CGPA conversion or assessment substitution.
    ssc_p: Score | None = None
    hsc_p: Score | None = None
    degree_p: Score | None = None
    etest_p: Score | None = None
    mba_p: Score | None = None
    gender: Literal["F", "M"] | None = None
    ssc_b: Literal["Central", "Others"] | None = None
    hsc_b: Literal["Central", "Others"] | None = None
    hsc_s: Literal["Arts", "Commerce", "Science"] | None = None
    degree_t: Literal["Comm&Mgmt", "Sci&Tech", "Others"] | None = None
    workex: Literal["No", "Yes"] | None = None
    specialisation: Literal["Mkt&Fin", "Mkt&HR"] | None = None

class PlacementModelFactor(BaseModel):
    key: str
    label: str
    value: float | str
    contribution: float

class PlacementModelSignal(BaseModel):
    available: bool
    score: float | None = None
    baseline: float | None = None
    breakdown: list[PlacementModelFactor] = Field(default_factory=list)
    explanation: str
    missing_fields: list[str] = Field(default_factory=list)
    methodology: str
    limitations: list[str]
    model_version: str | None = None

class PlacementModelEvaluation(BaseModel):
    dataset_rows: int
    train_rows: int
    test_rows: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: list[list[int]]
    source_url: str

class PlacementModelResponse(BaseModel):
    inputs: PlacementModelInput
    signal: PlacementModelSignal
    evaluation: PlacementModelEvaluation | None = None


class BTechModelInput(InputModel):
    cgpa: float | None = Field(default=None, ge=0, le=10, allow_inf_nan=False)
    stream: Literal["Civil", "Computer Science", "Electrical", "Electronics And Communication", "Information Technology", "Mechanical"] | None = None
    internships: int | None = Field(default=None, ge=0, le=100, strict=True)
    history_of_backlogs: int | None = Field(default=None, ge=0, le=1, strict=True)

class BTechModelEvaluation(PlacementModelEvaluation):
    distinct_profiles: int
    train_groups: int
    test_groups: int
    baseline_accuracy: float

class BTechModelResponse(BaseModel):
    inputs: BTechModelInput
    signal: PlacementModelSignal
    evaluation: BTechModelEvaluation | None = None


# Read-only student view over the existing keyword/weighted matching engine.
class OpportunityRole(BaseModel):
    job_id: int
    title: str
    company_name: str

class StudentOpportunity(MatchCalculation):
    job_id: int
    title: str
    company_name: str
    ctc: float
    min_cgpa: float
    max_backlogs: int
    eligible_branches: list[str]
    min_match_score: float

class StudentOpportunities(BaseModel):
    items: list[StudentOpportunity]
    target: StudentOpportunity | None
    roles: list[OpportunityRole]
    total: int
    eligible_count: int
    excluded_count: int
    offset: int
    limit: int
    calculated_at: datetime
    explanation: str

class CollegeReference(BaseModel):
    id: int
    name: str
    code: str | None
    district: str
    courses: list[str]
    category: str
    kind: Literal["demo", "bput_directory"]

class CollegeDirectory(BaseModel):
    source_url: str
    university_url: str
    source_year: str
    source_sha256: str
    note: str
    colleges: list[CollegeReference]

ApplicationStatus = Literal["submitted", "under_review", "shortlisted", "rejected", "withdrawn"]
class ApplicationSubmit(InputModel):
    job_id: int = Field(ge=1, strict=True)
    cover_note: str = Field(default="", max_length=1000)
class ApplicationAction(InputModel):
    version: int = Field(ge=1, strict=True)
    reason: str = Field(min_length=5, max_length=1000)
class ApplicationReview(ApplicationAction):
    status: Literal["under_review", "shortlisted", "rejected"]
class ApplicationEventResponse(BaseModel):
    id: int
    previous_status: ApplicationStatus | None
    status: ApplicationStatus
    reason: str
    created_at: datetime
class ApplicationResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    job_id: int
    job_title: str
    company_name: str
    status: ApplicationStatus
    cover_note: str
    version: int
    created_at: datetime
    updated_at: datetime
    evidence: MatchCalculation
    history: list[ApplicationEventResponse]
    explanation: str = "Submission-time weighted-rule evidence is frozen. Application review is a separate human decision, not an interview result or offer."
class ApplicationList(BaseModel):
    items: list[ApplicationResponse]
    total: int
    offset: int
    limit: int


class DetailResponse(BaseModel):
    detail: str
class EmailVerificationInput(InputModel):
    college_id: int = Field(ge=1, strict=True)
    token: str = Field(min_length=32, max_length=256)
class AccessRequestInput(InputModel):
    consent: Literal[True]
    affiliation_reference: str = Field(min_length=3, max_length=120)
    context: str = Field(default="", max_length=1000)
class AccessReviewInput(InputModel):
    version: int = Field(ge=1, strict=True)
    status: Literal["approved", "rejected"]
    reason: str = Field(min_length=5, max_length=1000)
class AccessEventResponse(BaseModel):
    id: int
    action: str
    reason: str
    created_at: datetime
class AccountAccessResponse(BaseModel):
    id: int | None
    college_id: int
    college_name: str
    email: str
    email_verified: bool
    email_delivery_ready: bool
    access_status: Literal["unverified", "pending", "approved", "rejected", "legacy_demo"]
    affiliation_reference: str
    context: str
    version: int
    requested_at: datetime | None
    history: list[AccessEventResponse]
    explanation: str = "Email verification confirms inbox access. A college administrator separately reviews affiliation; no automatic institution endorsement is implied."
class AccessQueueItem(AccountAccessResponse):
    name: str
    role: Literal["student", "recruiter"]
class AccessQueue(BaseModel):
    items: list[AccessQueueItem]
    total: int
    offset: int
    limit: int
class StudentInterviewResponse(InterviewResponse):
    job_title: str
    company_name: str
class InterviewListResponse(BaseModel):
    items: list[StudentInterviewResponse]
    total: int
    offset: int
    limit: int
class SchedulingApplicant(BaseModel):
    application_id: int
    job_id: int
    student_id: int
    job_title: str
    student_name: str

SchedulingBoard.model_rebuild()

# Targeted drive messages are plain-text, manually published in-app records.

AnnouncementAudience = Literal["applicants", "shortlisted", "scheduled", "college_students"]
AnnouncementKind = Literal["update", "reminder"]

class AnnouncementInput(InputModel):
    job_id: int = Field(gt=0, strict=True)
    audience: AnnouncementAudience
    branch: str | None = Field(default=None, min_length=1, max_length=80)
    kind: AnnouncementKind
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=10, max_length=4000)

    @field_validator("branch", mode="before")
    @classmethod
    def normalize_announcement_branch(cls, value):
        return " ".join(value.upper().split()) if isinstance(value, str) else value

class AnnouncementPublishInput(AnnouncementInput):
    preview_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    idempotency_key: UUID

class AnnouncementSample(BaseModel):
    student_id: int
    name: str
    branch: str

class AnnouncementOptions(BaseModel):
    jobs: list[NamedOption]
    branches: list[str]
    explanation: str

class AnnouncementPreviewResponse(AnnouncementInput):
    job_title: str
    company_name: str
    recipient_count: int
    sample: list[AnnouncementSample]
    preview_hash: str
    explanation: str

class AnnouncementResponse(AnnouncementInput):
    id: int
    job_title: str
    company_name: str
    published_by: int
    published_at: datetime
    recipient_count: int
    read_count: int
    explanation: str

class AnnouncementList(BaseModel):
    items: list[AnnouncementResponse]
    total: int
    offset: int
    limit: int

class AnnouncementRecipientResponse(AnnouncementSample):
    notification_id: int
    read_at: datetime | None

class AnnouncementRecipientList(BaseModel):
    items: list[AnnouncementRecipientResponse]
    total: int
    offset: int
    limit: int
    explanation: str
