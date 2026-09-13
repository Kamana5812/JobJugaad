'''Readiness Engine – weighted rule‑based calculation.
The formula follows ARCHITECTURE.md Section 5:
```
Readiness Score = 30% Technical Skills + 20% Projects +
                   15% Academics + 15% Aptitude +
                   10% Communication + 10% Interview
```
All inputs are expected on a 0‑100 scale. The engine returns a
dictionary that matches the `ReadinessResponse` schema: score, band,
breakdown, and a human‑readable explanation.
'''

from typing import Dict

# Band thresholds as per the spec
BANDS = [
    (0, 40, "Not Ready"),
    (41, 65, "Developing"),
    (66, 85, "Ready"),
    (86, 100, "Highly Employable"),
]

def _determine_band(score: float) -> str:
    for lo, hi, label in BANDS:
        if lo <= score <= hi:
            return label
    return "Unknown"

def calculate_readiness(student) -> Dict:
    """Compute readiness for a given Student ORM instance.

    Expected fields on `student` (0‑100 range, may be None):
        technical_score, project_score, cgpa, aptitude_score,
        communication_score, interview_score
    ``cgpa`` is used as the academic component after scaling to 0‑100
    (assuming a 10‑point CGPA scale; we map 0‑10 → 0‑100).
    """
    # Helper to safely get a value or default to 0
    def val(attr):
        v = getattr(student, attr, None)
        return float(v) if v is not None else 0.0

    # Technical & project scores are stored directly (0‑100)
    technical = val("technical_score")
    projects = val("project_score")

    # Academics uses CGPA (0‑10) → scale to 0‑100
    cgpa = val("cgpa")
    academics = (cgpa / 10.0) * 100.0 if cgpa else 0.0

    aptitude = val("aptitude_score")
    communication = val("communication_score")
    interview = val("interview_score")

    # Weighted sum (weights sum to 100)
    score = (
        technical * 0.30 +
        projects * 0.20 +
        academics * 0.15 +
        aptitude * 0.15 +
        communication * 0.10 +
        interview * 0.10
    )

    # Round to 1 decimal for display
    score = round(score, 1)
    band = _determine_band(score)

    breakdown = {
        "technical_skills": round(technical, 1),
        "projects": round(projects, 1),
        "academics": round(academics, 1),
        "aptitude": round(aptitude, 1),
        "communication": round(communication, 1),
        "interview": round(interview, 1),
    }

    # Build a concise explanation sentence.
    # We list the top three contributing factors.
    sorted_factors = sorted(breakdown.items(), key=lambda i: i[1], reverse=True)
    top_factors = ", ".join([f"{k.replace('_', ' ')} {v}" for k, v in sorted_factors[:3]])
    explanation = (
        f"Readiness score {score} ({band}); top contributors: {top_factors}."
    )

    # Store the computed score back on the student (optional persistence)
    student.readiness_score = score
    # Note: persistence is handled by caller if needed.

    return {
        "score": score,
        "band": band,
        "breakdown": breakdown,
        "explanation": explanation,
    }
