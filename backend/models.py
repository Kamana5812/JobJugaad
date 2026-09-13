'''SQLAlchemy ORM models for JobJugaad core entities.
All multi‑tenant tables include a `college_id` column (UUID) to support
application‑level filtering and a PostgreSQL Row‑Level Security (RLS)
policy (added in a startup hook).
'''

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

# Helper to generate UUID primary keys
def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # student|recruiter|admin
    college_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Student(Base):
    __tablename__ = "students"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    branch = Column(String, nullable=True)
    cgpa = Column(Float, nullable=True)
    backlog_count = Column(Integer, nullable=True)
    resume_text = Column(String, nullable=True)
    # Scores used by the readiness engine (0‑100 scale)
    technical_score = Column(Float, nullable=True)
    project_score = Column(Float, nullable=True)
    aptitude_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    readiness_score = Column(Float, nullable=True)
    college_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentSkill(Base):
    __tablename__ = "student_skills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    proficiency = Column(Integer, nullable=False)  # 0‑100
    college_id = Column(UUID(as_uuid=True), nullable=False)

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    college_id = Column(UUID(as_uuid=True), nullable=False)

class Certification(Base):
    __tablename__ = "certifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    college_id = Column(UUID(as_uuid=True), nullable=False)
