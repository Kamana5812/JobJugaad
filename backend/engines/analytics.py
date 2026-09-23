"""Actual shortlist conversion counts; offer/placement outcomes are not yet tracked."""
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import select
from models import Student, User, Job, Match, StudentSkill
from schemas import AnalyticsResponse, ConversionRow
from engines.skill_gap import normalize_skill


def overview(session, user):
    college = user.college_id
    students = session.scalars(select(Student).where(Student.college_id == college)).all()
    recruiter_ids = session.scalars(select(User.id).where(User.college_id == college, User.role == "recruiter")).all()
    jobs = session.scalars(select(Job).where(Job.college_id == college)).all()
    matches = session.scalars(select(Match).where(Match.college_id == college)).all()
    shortlisted = {m.student_id for m in matches if m.override_action == "promote" or (m.override_action is None and m.eligible)}
    branches, skills = defaultdict(set), defaultdict(set)
    for student in students:
        branches[student.branch].add(student.id)
    for skill in session.scalars(select(StudentSkill).where(StudentSkill.college_id == college)):
        skills[normalize_skill(skill.skill_name)].add(skill.student_id)
    def rows(groups):
        return [ConversionRow(name=name, total_students=len(ids), shortlisted_students=len(ids & shortlisted),
            conversion_percent=round(len(ids & shortlisted) / len(ids) * 100, 2) if ids else None)
            for name, ids in sorted(groups.items())]
    ctc = [float(j.ctc) for j in jobs]
    return AnalyticsResponse(students=len(students), recruiters=len(recruiter_ids), drives=len(jobs),
        placement_percent=None, placement_explanation="Placement outcomes are not tracked yet. Offer records begin in Phase 4; no placement percentage is inferred from a shortlist or interview selection.",
        branch_conversion=rows(branches), skill_conversion=rows(skills),
        ctc_min_lpa=min(ctc) if ctc else None, ctc_max_lpa=max(ctc) if ctc else None,
        ctc_mean_lpa=round(sum(ctc)/len(ctc),2) if ctc else None,
        methodology="Shortlist conversion = distinct students shortlisted for at least one drive / all recorded students in that branch or skill group. Includes documented human overrides and current saved matching snapshots. It is not placement conversion. CTC figures describe advertised drives, not accepted offers.",
        generated_at=datetime.now(timezone.utc))
