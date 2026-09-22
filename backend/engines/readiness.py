"""Proposed weighted rule, not AI/ML or a validated hiring assessment."""
from decimal import Decimal, ROUND_HALF_UP
from schemas import FactorResponse, ReadinessResponse

WEIGHTS = (30, 20, 15, 15, 10, 10)
LABELS = ("Technical skills", "Projects", "Academics", "Aptitude", "Communication", "Interview")
KEYS = ("technical_skills", "projects", "academics", "aptitude", "communication", "interview")
NEXT_STEPS = (
    "Record your current skills and practise the ones you want to strengthen.",
    "Add a project with a clear description of what you built and contributed.",
    "Check that your current CGPA is recorded accurately.",
    "Record an existing aptitude assessment or ask your placement cell for practice guidance.",
    "Practise a short project explanation and record existing communication feedback.",
    "Record feedback from an existing interview assessment; no interview is conducted here.",
)

def calculate_readiness(student, skills, projects) -> ReadinessResponse:
    # Explicit starting assumptions: average proficiency, 25 points/project,
    # CGPA x 10. Existing assessment results are already on the 0-100 scale.
    values = [sum(s.proficiency for s in skills) / len(skills) if skills else 0,
        min(len(projects) * 25, 100), (student.cgpa or 0) * 10,
        student.aptitude_score or 0, student.communication_score or 0, student.interview_score or 0]
    missing = [not skills, not projects, student.cgpa is None, student.aptitude_score is None,
        student.communication_score is None, student.interview_score is None]
    evidence = [
        f"Mean of {len(skills)} self-reported skill proficiencies." if skills else "No skills recorded; contributes zero.",
        f"{len(projects)} recorded projects x 25 points, capped at 100; quality is not assessed.",
        f"CGPA {student.cgpa:g}/10 x 10." if student.cgpa is not None else "CGPA not recorded; contributes zero.",
    ] + [f"Self-reported existing assessment: {v:g}/100." if not absent else "Assessment not recorded; contributes zero."
         for v, absent in zip(values[3:], missing[3:])]
    factors, total = [], Decimal("0")
    for key, label, value, weight, reason, absent in zip(KEYS, LABELS, values, WEIGHTS, evidence, missing):
        value_decimal = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        contribution = (value_decimal * weight / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += contribution
        factors.append(FactorResponse(key=key, label=label, value=float(value_decimal), weight=weight,
            contribution=float(contribution), evidence=reason, missing=absent))
    score = int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    band = "Not Ready" if score <= 40 else "Developing" if score <= 65 else "Ready" if score <= 85 else "Highly Employable"
    strongest = max(range(6), key=lambda i: values[i])
    weakest = min(range(6), key=lambda i: values[i])
    explanation = (f"Your recorded profile totals {score}/100 ({band}) under this weighted rule; "
        f"{LABELS[strongest].lower()} is your strongest recorded factor and "
        f"{LABELS[weakest].lower()} is a useful next area to review.") if score else (
        "Your profile currently contributes 0/100 (Not Ready); add profile evidence to build a useful readiness view.")
    if any(missing):
        explanation += " Missing information contributes zero, which is not a judgment of your ability."
    return ReadinessResponse(score=score, raw_score=float(total), band=band, breakdown=factors,
        explanation=explanation, next_step=NEXT_STEPS[weakest],
        methodology="Proposed weighted rule: 30/20/15/15/10/10; self-reported inputs, not a trained model or validated hiring prediction. Round the total half-up to a whole number before band mapping.")
