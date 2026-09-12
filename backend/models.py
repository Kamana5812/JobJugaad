from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # "student", "recruiter", "admin"
    college_id = Column(String, default="default_college")
    created_at = Column(DateTime, default=datetime.utcnow)

    student_profile = relationship("Student", back_populates="user", uselist=False)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    branch = Column(String)
    cgpa = Column(Float)
    backlog_count = Column(Integer, default=0)
    resume_text = Column(Text, nullable=True)
    
    # Mock scores
    aptitude_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    interview_score = Column(Float, default=0.0)
    
    readiness_score = Column(Float, default=0.0)
    college_id = Column(String, default="default_college")

    user = relationship("User", back_populates="student_profile")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="student", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="student", cascade="all, delete-orphan")

class StudentSkill(Base):
    __tablename__ = "student_skills"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    skill_name = Column(String)
    proficiency = Column(Integer) # 0-100

    student = relationship("Student", back_populates="skills")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    title = Column(String)
    description = Column(Text)

    student = relationship("Student", back_populates="projects")

class Certification(Base):
    __tablename__ = "certifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    title = Column(String)
    description = Column(Text)

    student = relationship("Student", back_populates="certifications")
