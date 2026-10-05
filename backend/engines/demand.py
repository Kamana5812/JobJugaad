"""Recorded hiring demand and lifecycle counts; no prediction or borrowed market claim."""
from collections import Counter, defaultdict
from fastapi import HTTPException
from sqlalchemy import select
from models import Job, Company, Application, Interview, Offer
from engines.talent import owned_company

def report(session, user):
    if user.role not in {'recruiter', 'admin'}:
        raise HTTPException(403, 'College staff or recruiter access required.')
    query = select(Job).where(Job.college_id == user.college_id)
    if user.role == 'recruiter':
        company = owned_company(session, user)
        query = query.where(Job.company_id == company.id)
    jobs = session.scalars(query.order_by(Job.id.desc())).all()
    ids = [job.id for job in jobs]
    applications, selected, accepted, joined = defaultdict(set), defaultdict(set), defaultdict(set), defaultdict(set)
    active, shortlist = defaultdict(set), defaultdict(set)
    for row in session.scalars(select(Application).where(Application.college_id == user.college_id, Application.job_id.in_(ids))):
        applications[row.job_id].add(row.student_id)
        if row.status in ('submitted', 'under_review', 'shortlisted'):
            active[row.job_id].add(row.student_id)
        if row.status == 'shortlisted':
            shortlist[row.job_id].add(row.student_id)
    for row in session.scalars(select(Interview).where(Interview.college_id == user.college_id,
        Interview.job_id.in_(ids), Interview.event_type == 'interview', Interview.status == 'selected')):
        selected[row.job_id].add(row.student_id)
    for row in session.scalars(select(Offer).where(Offer.college_id == user.college_id, Offer.job_id.in_(ids))):
        if row.acceptance_status == 'accepted':
            accepted[row.job_id].add(row.student_id)
        if row.joining_status == 'joined':
            joined[row.job_id].add(row.student_id)
    skills = Counter(' '.join(skill['skill_name'].lower().split()) for job in jobs if job.is_open
        for skill in job.required_skills)
    return {'scope': 'Your company in this college' if user.role == 'recruiter' else 'Recorded drives in your college',
        'open_drives': sum(job.is_open for job in jobs), 'total_drives': len(jobs),
        'skills': [{'skill_name': skill, 'open_drive_count': count} for skill, count in sorted(skills.items(), key=lambda pair: (-pair[1], pair[0]))],
        'drives': [{'job_id': job.id, 'title': job.title, 'is_open': job.is_open,
            'submitted': len(applications[job.id]), 'active_applications': len(active[job.id]),
            'shortlisted': len(shortlist[job.id]), 'selected': len(selected[job.id]),
            'accepted': len(accepted[job.id]), 'joined': len(joined[job.id])} for job in jobs],
        'explanation': 'Recorded counts, not a market forecast. Each stage counts distinct student-drive pairs, so repeated interview rounds do not inflate selections. Stages are independent milestones, not guaranteed nested cohorts; withdrawals and later changes can affect current totals. Skill demand counts open drives mentioning a reviewed requirement. Archive/synthetic drives retain their original provenance.'}
