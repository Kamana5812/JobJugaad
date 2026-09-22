"""Proposed weighted rule with exact keywords; no trained model or confidence.

Starting 40/20/20/15/5 weights and normalization choices are UNVALIDATED
ASSUMPTIONS, not empirically tuned. Each component is normalized to 0-100.
Experience is omitted because no structured experience field is collected.
"""
import re
from decimal import Decimal, ROUND_HALF_UP
from engines.skill_gap import skill_gaps
from schemas import MatchCalculation

METHODOLOGY = ("Proposed weighted rule using exact skill keywords, project keyword coverage, "
    "CGPA x 10, the mean of three self-reported assessments (missing = 0), and a capped "
    "certificate-count proxy. Components are normalized to 0-100. Weights and thresholds "
    "are unvalidated assumptions; no trained model, calibrated confidence, or accuracy claim.")


def rounded(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def hard_requirements(student, job):
    reasons = []
    if student.cgpa is None or student.cgpa < job.min_cgpa:
        reasons.append(f"CGPA {'not recorded' if student.cgpa is None else format(student.cgpa, 'g')} does not meet {job.min_cgpa:g}/10")
    if " ".join(student.branch.upper().split()) not in job.eligible_branches:
        reasons.append(f"branch {student.branch} is outside {', '.join(job.eligible_branches)}")
    if student.backlog_count > job.max_backlogs:
        reasons.append(f"backlog count {student.backlog_count} exceeds {job.max_backlogs}")
    return reasons


def calculate_match(student, skills, projects, certifications, job):
    hard = hard_requirements(student, job)  # Eligibility checked before shortlist ranking.
    gaps = skill_gaps(skills, job.required_skills)
    skill_value = sum(min(g["proficiency"] / g["required"], 1) * 100 for g in gaps) / len(gaps)
    project_text = " ".join(f"{p.title} {p.description}" for p in projects).lower()
    covered = sum(bool(re.search(r"(?<!\w)" + re.escape(g["skill_name"]) + r"(?!\w)", project_text)) for g in gaps)
    assessments = [student.aptitude_score, student.communication_score, student.interview_score]
    assessment_value = sum(v or 0 for v in assessments) / 3
    values = [
        ("skills", "Skill compatibility", skill_value, f"Mean capped proficiency/target across {len(gaps)} exact skill names; {sum(g['status'] == 'on-track' for g in gaps)} targets met.", not skills),
        ("projects", "Project relevance", covered / len(gaps) * 100, f"{covered}/{len(gaps)} required keywords appear in recorded projects; keyword evidence is not a quality assessment.", not projects),
        ("academics", "Academics", (student.cgpa or 0) * 10, f"CGPA {student.cgpa if student.cgpa is not None else 'missing'}/10 multiplied by 10.", student.cgpa is None),
        ("assessments", "Assessment performance", assessment_value, f"Mean of aptitude, communication and existing interview inputs; {sum(v is None for v in assessments)} missing input(s) contribute zero. Self-reported.", any(v is None for v in assessments)),
        ("certifications", "Certifications", min(len(certifications) * 25, 100), f"{len(certifications)} recorded certificates, 25 points each capped at 100; count proxy, not credential verification.", not certifications),
    ]
    factors = [dict(key=key, label=label, value=rounded(value), weight=job.weights[key],
        contribution=rounded(rounded(value) * job.weights[key] / 100), evidence=evidence, missing=missing)
        for key, label, value, evidence, missing in values]
    score = rounded(sum(f["contribution"] for f in factors))
    low = score < job.min_match_score
    deficient = [g for g in gaps if g["status"] != "on-track"]
    missing = hard + [f"{g['skill_name']} proficiency {g['proficiency']:g}/100 is below target {g['required']:g}/100" for g in deficient]
    if low:
        missing.append(f"weighted match score {score:g}/100 is below the {job.min_match_score:g}/100 threshold")
    if assessment_value < job.assessment_benchmark:
        missing.append(f"assessment mean {assessment_value:g}/100 is below the review benchmark {job.assessment_benchmark:g}/100")
    eligible = not hard and not low
    academic = "CGPA meets the eligibility criteria" if student.cgpa is not None and student.cgpa >= job.min_cgpa else hard[0]
    other = hard[-1] if hard else f"the weighted match score {score:g}/100 is below the required {job.min_match_score:g}/100 threshold"
    if not eligible and deficient:
        explanation = (f"Below Threshold: The student's {academic}, but the required skill set shows a gap in "
            f"{deficient[0]['skill_name']} and {other}.")
    elif not eligible:
        # Fixed truthful variant: never invent a skill gap when all targets are met.
        explanation = (f"Below Threshold: The student's {academic}, but no required skill gap was found and {other}.")
    else:
        explanation = (f"Eligible for review: The student meets the CGPA, branch and backlog rules, "
            f"with {score:g}/100 against the {job.min_match_score:g}/100 threshold; "
            f"{len(gaps) - len(deficient)}/{len(gaps)} skill targets are met.")
    next_step = deficient[0]["next_step"] if deficient else "Review and update the recorded profile evidence with the student."
    if hard:
        next_step += " Ask a recruiter to review the stated eligibility restriction; a manual exception must be recorded."
    return MatchCalculation(match_score=score, factor_breakdown=factors, missing_requirements=missing,
        skill_gaps=gaps, eligible=eligible, explanation=explanation, next_step=next_step, methodology=METHODOLOGY)
