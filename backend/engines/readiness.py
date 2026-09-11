from typing import Dict

# Weight percentages for each factor (must sum to 100)
WEIGHTS = {
    "technical": 30,
    "projects": 20,
    "academics": 15,
    "aptitude": 15,
    "communication": 10,
    "interview": 10,
}

def _average_skill_proficiency(student) -> float:
    # student.skills is a list of ORM objects with 'proficiency' attribute (0‑100)
    if not student.skills:
        return 0.0
    total = sum(skill.proficiency for skill in student.skills)
    return total / len(student.skills)

def _projects_score(student) -> float:
    # Simple heuristic: each project contributes up to 10 points, capped at 100
    count = len(student.projects) if hasattr(student, "projects") else 0
    return min(count * 10.0, 100.0)

def _academics_score(student) -> float:
    # Assume cgpa out of 10; scale to 0‑100
    return min(max(student.cgpa, 0.0) * 10.0, 100.0)

def calculate_readiness(student) -> Dict:
    """Calculate the readiness score for a student.

    Returns a dict with keys: score, band, explanation, breakdown.
    """
    # Gather individual factor scores (0‑100)
    technical = _average_skill_proficiency(student)
    projects = _projects_score(student)
    academics = _academics_score(student)
    aptitude = getattr(student, "aptitude_score", 0.0)
    communication = getattr(student, "communication_score", 0.0)
    interview = getattr(student, "interview_score", 0.0)

    # Weighted sum (each factor already 0‑100, weight is percent)
    total = (
        technical * WEIGHTS["technical"]
        + projects * WEIGHTS["projects"]
        + academics * WEIGHTS["academics"]
        + aptitude * WEIGHTS["aptitude"]
        + communication * WEIGHTS["communication"]
        + interview * WEIGHTS["interview"]
    ) / 100.0

    # Determine band
    if total <= 40:
        band = "Not Ready"
    elif total <= 65:
        band = "Developing"
    elif total <= 85:
        band = "Ready"
    else:
        band = "Highly Employable"

    # Simple explanation based on low‑scoring factors
    low_factors = []
    if technical < 50:
        low_factors.append("technical skills")
    if projects < 50:
        low_factors.append("project experience")
    if academics < 50:
        low_factors.append("academics")
    if aptitude < 50:
        low_factors.append("aptitude test")
    if communication < 50:
        low_factors.append("communication")
    if interview < 50:
        low_factors.append("interview performance")

    if low_factors:
        explanation = f"Improve: {', '.join(low_factors)}."
    else:
        explanation = "All factors look strong. Keep up the good work!"

    breakdown = {
        "technical": technical,
        "projects": projects,
        "academics": academics,
        "aptitude": aptitude,
        "communication": communication,
        "interview": interview,
    }

    return {
        "score": total,
        "band": band,
        "explanation": explanation,
        "breakdown": breakdown,
    }
