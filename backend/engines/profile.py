"""Profile persistence with explicit college filters on every tenant-table query."""
from sqlalchemy import select, delete, update
from models import Student, StudentSkill, Project, Certification
from schemas import ProfileResponse, SkillInput, EvidenceInput
from engines.readiness import calculate_readiness

COLLECTIONS = {"skills": StudentSkill, "projects": Project, "certifications": Certification}

def collections(session, student):
    return {key: list(session.scalars(select(model).where(model.student_id == student.id,
        model.college_id == student.college_id).order_by(model.id))) for key, model in COLLECTIONS.items()}

def profile_response(session, student):
    data = collections(session, student)
    return ProfileResponse(id=student.id, user_id=student.user_id, college_id=student.college_id,
        name=student.name, branch=student.branch, cgpa=student.cgpa, backlog_count=student.backlog_count,
        aptitude_score=student.aptitude_score, communication_score=student.communication_score,
        interview_score=student.interview_score, resume_text=student.resume_text,
        skills=[SkillInput(skill_name=s.skill_name, proficiency=s.proficiency) for s in data["skills"]],
        projects=[EvidenceInput(title=p.title, description=p.description) for p in data["projects"]],
        certifications=[EvidenceInput(title=c.title, description=c.description) for c in data["certifications"]],
        readiness=calculate_readiness(student, data["skills"], data["projects"]))

def update_fields(session, student, fields):
    session.execute(update(Student).where(Student.id == student.id, Student.college_id == student.college_id,
        Student.user_id == student.user_id).values(**fields))
    # ORM synchronization updates the already scoped in-memory instance too.
    session.flush()

def save_profile(session, student, payload):
    update_fields(session, student, payload.model_dump(exclude=set(COLLECTIONS)))
    for key, model in COLLECTIONS.items():
        session.execute(delete(model).where(model.student_id == student.id, model.college_id == student.college_id))
        session.add_all([model(student_id=student.id, college_id=student.college_id, **item.model_dump())
            for item in getattr(payload, key)])
    session.flush()
    response = profile_response(session, student)
    update_fields(session, student, {"readiness_score": response.readiness.score})
    return response
