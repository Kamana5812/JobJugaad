"""Counts from recorded offers/matches; synthetic records remain explicitly labeled."""
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import select, or_, and_
from models import Student, User, Job, Match, StudentSkill, Offer
from schemas import AnalyticsResponse, ConversionRow
from engines.skill_gap import normalize_skill


def overview(session, user):
    college = user.college_id
    students = session.execute(select(Student.id,Student.branch).where(Student.college_id == college)).all()
    recruiters = session.scalars(select(User.id).where(User.college_id == college, User.role == "recruiter")).all()
    ctc = [float(v) for v in session.scalars(select(Job.ctc).where(Job.college_id == college))]
    shortlisted = set(session.scalars(select(Match.student_id).where(Match.college_id == college,
        or_(Match.override_action == "promote",and_(Match.override_action.is_(None),Match.eligible.is_(True))))))
    branches, skills = defaultdict(set), defaultdict(set)
    for student in students:
        branches[student.branch].add(student.id)
    for skill in session.execute(select(StudentSkill.student_id,StudentSkill.skill_name).where(StudentSkill.college_id == college)):
        skills[normalize_skill(skill.skill_name)].add(skill.student_id)
    def rows(groups):
        return [ConversionRow(name=name,total_students=len(ids),shortlisted_students=len(ids & shortlisted),
            conversion_percent=round(len(ids & shortlisted)/len(ids)*100,2) if ids else None) for name,ids in sorted(groups.items())]
    offers=session.execute(select(Offer.student_id,Offer.ctc,Offer.offer_letter_status,Offer.acceptance_status,Offer.joining_status,Offer.is_synthetic)
        .where(Offer.college_id == college)).all()
    accepted=[o for o in offers if o.offer_letter_status == "issued" and o.acceptance_status == "accepted" and o.joining_status != "not_joined"]
    accepted_ids={o.student_id for o in accepted}
    joined_ids={o.student_id for o in accepted if o.joining_status == "joined"}
    accepted_ctc=[float(o.ctc) for o in accepted]
    return AnalyticsResponse(students=len(students),recruiters=len(recruiters),drives=len(ctc),
        placement_percent=round(len(accepted_ids)/len(students)*100,2) if students else None,
        placement_explanation=f"Recorded placement proxy: {len(accepted_ids)} distinct students with an issued, accepted offer not marked not joined / {len(students)} recorded students. This is not proof of joining; {len(joined_ids)} students have joining recorded. Includes labeled synthetic demo offers.",
        branch_conversion=rows(branches),skill_conversion=rows(skills),
        ctc_min_lpa=min(ctc) if ctc else None,ctc_max_lpa=max(ctc) if ctc else None,
        ctc_mean_lpa=round(sum(ctc)/len(ctc),2) if ctc else None,
        accepted_students=len(accepted_ids),joined_students=len(joined_ids),offer_count=len(offers),
        synthetic_offer_count=sum(o.is_synthetic for o in offers),
        accepted_ctc_min_lpa=min(accepted_ctc) if accepted_ctc else None,
        accepted_ctc_max_lpa=max(accepted_ctc) if accepted_ctc else None,
        accepted_ctc_mean_lpa=round(sum(accepted_ctc)/len(accepted_ctc),2) if accepted_ctc else None,
        methodology="Shortlist conversion = distinct students shortlisted for at least one drive / all recorded students in each branch or skill group, including human overrides and saved match snapshots. Placement uses recorded active accepted offers; joining is separate. Advertised CTC is per drive; accepted CTC is per qualifying offer, so students with multiple offers may appear more than once in those package statistics. Synthetic records are demonstration data, not real placement outcomes.",
        generated_at=datetime.now(timezone.utc))
