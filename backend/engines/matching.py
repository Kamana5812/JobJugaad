"""Matching Engine – rule‑based, explainable candidate ranking.

The implementation follows the unvalidated starting weights documented in ARCHITECTURE.md §5.
All components are normalized to a 0‑100 scale before weighting. No confidence score is reported.
"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json

from backend import models, schemas

# Unvalidated starting weights – these are assumptions, not empirically tuned.
SKILL_WEIGHT = 0.4
CGPA_WEIGHT = 0.3
ASSESSMENT_WEIGHT = 0.3
ELIGIBILITY_THRESHOLD = 60.0  # minimum final score for inclusion

def _normalize_cgpa(cgpa: float | None) -> float:
    if cgpa is None:
        return 0.0
    # CGPA is on a 0‑10 scale; map to 0‑100
    return max(0.0, min(100.0, (cgpa / 10.0) * 100.0))

def _average_assessment(student) -> float:
    # Average of technical, project, aptitude, communication, interview scores (0‑100 each)
    scores = [
        getattr(student, "technical_score", 0) or 0,
        getattr(student, "project_score", 0) or 0,
        getattr(student, "aptitude_score", 0) or 0,
        getattr(student, "communication_score", 0) or 0,
        getattr(student, "interview_score", 0) or 0,
    ]
    # Filter out None values (already replaced with 0)
    return sum(scores) / len(scores) if scores else 0.0

def _skill_overlap(student_id: str, required_skills: dict, db: Session) -> tuple[float, dict, List[str]]:
    """Calculate skill overlap (0‑100) and gap status.

    Returns:
        overlap_score: average percentage of required skill met (capped at 100)
        gap_status: mapping skill -> "on-track"|"gap"|"critical"
        missing: list of skill names that are missing or below requirement
    """
    if not required_skills:
        return 0.0, {}, []
    # Fetch all student skill rows for this student
    rows = db.query(models.StudentSkill).filter(models.StudentSkill.student_id == student_id).all()
    skill_map = {row.skill_name: row.proficiency for row in rows}
    scores = []
    gap_status = {}
    missing = []
    for skill, req in required_skills.items():
        stud_val = skill_map.get(skill, 0)
        # Overlap as percentage of requirement, capped at 100
        overlap = (stud_val / req) * 100.0 if req > 0 else 0.0
        overlap = min(overlap, 100.0)
        scores.append(overlap)
        # Determine gap status
        if stud_val >= req:
            status = "on-track"
        elif stud_val >= req * 0.5:
            status = "gap"
        else:
            status = "critical"
        gap_status[skill] = status
        if status != "on-track":
            missing.append(skill)
    overlap_score = sum(scores) / len(scores) if scores else 0.0
    return overlap_score, gap_status, missing

def _eligibility_checks(student, job) -> List[str]:
    """Return a list of reasons why the student is ineligible.
    Empty list means the student passes hard filters.
    """
    reasons = []
    # Branch check
    if job.eligible_branches:
        if not student.branch or student.branch not in job.eligible_branches:
            reasons.append("branch not eligible")
    # CGPA minimum check
    if job.min_cgpa is not None:
        if not student.cgpa or student.cgpa < job.min_cgpa:
            reasons.append("CGPA below minimum")
    return reasons

def run_matching(job_id: str, db: Session, payload: dict) -> List[schemas.MatchRead]:
    """Execute the matching algorithm for a given job.

    Returns a list of MatchRead objects (including excluded candidates with
    explanations following the required template).
    """
    # Load job (RLS ensures same college)
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise ValueError("Job not found")
    # Load all students in the same college (RLS filters automatically)
    students = db.query(models.Student).all()
    # Load existing matches to preserve manual overrides
    existing_matches = {m.student_id: m for m in db.query(models.Match).filter(models.Match.job_id == job_id).all()}
    
    matches: List[schemas.MatchRead] = []
    for student in students:
        # Hard eligibility
        hard_reasons = _eligibility_checks(student, job)
        # Skill overlap & gap analysis
        overlap_score, gap_status, missing_skills = _skill_overlap(student.id, job.required_skills or {}, db)
        cgpa_norm = _normalize_cgpa(student.cgpa)
        assessment_score = _average_assessment(student)
        # Compute weighted score
        match_score = (
            overlap_score * SKILL_WEIGHT +
            cgpa_norm * CGPA_WEIGHT +
            assessment_score * ASSESSMENT_WEIGHT
        )
        match_score = round(match_score, 1)
        # Determine if student passes threshold and hard filters
        excluded = False
        missing_requirements: dict = {}
        explanation = None
        if hard_reasons:
            excluded = True
            missing_requirements["hard_filters"] = hard_reasons
        if match_score < ELIGIBILITY_THRESHOLD:
            excluded = True
            missing_requirements.setdefault("score", []).append("below threshold")
        if missing_skills:
            # Include skill gaps in missing_requirements
            missing_requirements.setdefault("skill_gaps", []).extend(missing_skills)
        if excluded:
            # Build explanation according to required pattern
            # Choose one primary reason for the sentence
            primary_reason = hard_reasons[0] if hard_reasons else "overall score below threshold"
            # Pick two missing skills for the template (if any)
            skill_examples = missing_skills[:2]
            skill_part = " and ".join(skill_examples) if skill_examples else "none"
            explanation = f"Below Threshold: The student's {primary_reason}, but the required skill set shows a gap in {skill_part}."
        # Upsert match record
        match_record = existing_matches.get(student.id)
        if not match_record:
            match_record = models.Match(
                job_id=job.id,
                student_id=student.id,
                college_id=payload["college_id"]
            )
            db.add(match_record)
            
        match_record.match_score = match_score
        match_record.factor_breakdown = {
            "skill_overlap": round(overlap_score, 1),
            "cgpa": round(cgpa_norm, 1),
            "assessment": round(assessment_score, 1),
        }
        match_record.missing_requirements = missing_requirements or None
        match_record.explanation = explanation
        
        db.flush()  # get ID without committing yet
        # Build response object
        matches.append(schemas.MatchRead(
            id=match_record.id,
            job_id=job.id,
            student_id=student.id,
            match_score=match_score,
            factor_breakdown=match_record.factor_breakdown,
            missing_requirements=match_record.missing_requirements,
            explanation=explanation,
            override_status=match_record.override_status,
        ))
    db.commit()
    # Sort matches descending by score (included and excluded are both in list)
    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches
