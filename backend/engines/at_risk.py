"""At-Risk Engine

A simple rule-based engine to flag students who are at risk of not being placed.
This intentionally avoids LLMs or trained ML classifiers in Phase 3.
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend import models

def evaluate_student(student: models.Student, db: Session) -> Dict[str, Any]:
    """Evaluates a student against simple rule-based thresholds.
    
    Returns a dict with:
    - is_at_risk: bool
    - factors: List[str]
    - recommendation: str (if at risk)
    """
    factors = []
    
    # Rule 1: Backlogs
    if student.backlog_count and student.backlog_count > 0:
        factors.append(f"Student has {student.backlog_count} active backlogs")
        
    # Rule 2: Low mock interview score
    if student.interview_score is None or student.interview_score < 60:
        factors.append("Mock interview score is below 60")
        
    # Rule 3: Low overall readiness
    if student.readiness_score is not None and student.readiness_score < 60:
        factors.append("Overall readiness score is below 60")
        
    # Rule 4: Skill gaps (less than 2 skills above 60 proficiency)
    skills = db.query(models.StudentSkill).filter(models.StudentSkill.student_id == student.id).all()
    strong_skills = [s for s in skills if s.proficiency >= 60]
    if len(strong_skills) < 2:
        factors.append("Lacks at least 2 strong core skills (proficiency >= 60)")

    # The student is flagged if they trigger 2 or more risk factors
    is_at_risk = len(factors) >= 2
    
    recommendation = None
    if is_at_risk:
        if student.backlog_count and student.backlog_count > 0:
            recommendation = "Schedule mandatory academic counseling to clear backlogs."
        elif student.interview_score is None or student.interview_score < 60:
            recommendation = "Enroll in the upcoming weekend mock interview workshop."
        else:
            recommendation = "Assign to a technical mentor for skill upskilling."

    return {
        "student_id": str(student.id),
        "student_name": student.name,
        "is_at_risk": is_at_risk,
        "factors": factors if is_at_risk else [],
        "recommendation": recommendation
    }
