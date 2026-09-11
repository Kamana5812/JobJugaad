from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)
    college_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # One-to-one relationship with Student (if role is student)
    student = relationship("Student", back_populates="user", uselist=False)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    cgpa = Column(Float, nullable=False)
    backlog_count = Column(Integer, default=0)
    resume_text = Column(Text, nullable=True)
    aptitude_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    interview_score = Column(Float, default=0.0)
    readiness_score = Column(Float, default=0.0)
    college_id = Column(Integer, nullable=True)

    user = relationship("User", back_populates="student")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="student", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="student", cascade="all, delete-orphan")

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    recruiter = relationship("User", backref="companies")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String, nullable=False)
    ctc = Column(Float, nullable=False)
    min_cgpa = Column(Float, nullable=False)
    eligible_branches = Column(String, nullable=False)  # comma‑separated
    required_skills = Column(String, nullable=False)   # comma‑separated
    company = relationship("Company", back_populates="jobs")

class StudentSkill(Base):
    __tablename__ = "student_skills"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    proficiency = Column(Integer, default=0)  # 0‑100

    student = relationship("Student", back_populates="skills")

# Extend Company relationship
Company.jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    student = relationship("Student", back_populates="projects")

class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    institution = Column(String, nullable=True)
    year = Column(Integer, nullable=True)

    student = relationship("Student", back_populates="certifications")
