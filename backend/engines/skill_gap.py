"""Skill Gap Engine

Calculates on-track/gap/critical status for a student against a specific role.
For MVP, role requirements are hardcoded here.
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from backend import models

# Hardcoded MVP roles for demonstration
ROLE_REQUIREMENTS = {
    "Software Engineer": {
        "Python": 80,
        "Java": 70,
        "SQL": 60,
    },
    "Data Analyst": {
        "SQL": 80,
        "Python": 70,
        "Excel": 60,
    },
    "Frontend Developer": {
        "React": 80,
        "Node.js": 60,
        "JavaScript": 85,
    }
}

def analyze_skill_gap(student_id: str, role: str, db: Session) -> Dict[str, Any]:
    """Analyzes a student's skills against a target role.
    
    Returns a dictionary indicating the status of each required skill.
    Status can be: 'on-track', 'gap', or 'critical'.
    """
    requirements = ROLE_REQUIREMENTS.get(role)
    if not requirements:
        raise ValueError(f"Role '{role}' is not supported. Supported roles: {', '.join(ROLE_REQUIREMENTS.keys())}")
        
    student_skills_records = db.query(models.StudentSkill).filter(
        models.StudentSkill.student_id == student_id
    ).all()
    
    student_skill_map = {record.skill_name: record.proficiency for record in student_skills_records}
    
    analysis = {}
    for req_skill, req_level in requirements.items():
        actual_level = student_skill_map.get(req_skill, 0)
        
        if actual_level >= req_level:
            status = "on-track"
        elif actual_level >= req_level * 0.5:
            status = "gap"
        else:
            status = "critical"
            
        analysis[req_skill] = {
            "required": req_level,
            "actual": actual_level,
            "status": status
        }
        
    return {
        "role": role,
        "analysis": analysis
    }
