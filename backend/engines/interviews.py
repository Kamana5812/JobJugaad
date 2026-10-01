"""Student-owned calendar records; proposals and other students' bookings remain private."""
from sqlalchemy import select, func
from models import Interview, Job, Company
from schemas import InterviewResponse, InterviewListResponse, StudentInterviewResponse


def interviews_for_student(session, student, offset, limit):
    college = student.college_id
    query = select(Interview, Job.title, Company.name).join(Job,
        (Job.id == Interview.job_id) & (Job.college_id == Interview.college_id)).join(Company,
        (Company.id == Job.company_id) & (Company.college_id == Job.college_id)).where(
        Interview.college_id == college, Interview.student_id == student.id,
        Job.college_id == college, Company.college_id == college)
    total = session.scalar(select(func.count()).select_from(query.subquery()))
    rows = session.execute(query.order_by(Interview.scheduled_time.desc(), Interview.id.desc()).offset(offset).limit(limit)).all()
    return InterviewListResponse(items=[StudentInterviewResponse(
        **InterviewResponse.model_validate(row, from_attributes=True).model_dump(), job_title=title, company_name=name)
        for row, title, name in rows], total=total, offset=offset, limit=limit)
