"""Proposed support thresholds only; NOT a trained classifier or failure forecast.

Any later classifier requires SMOTE or class weighting and imbalance-aware
evaluation. Explicitly remind the user of this prerequisite before an upgrade.
"""
from engines.skill_gap import skill_gaps
from schemas import SupportCalculation

METHOD = ("Proposed deterministic AND rule: at least 3 skill gaps for the selected role, "
    "a recorded interview score below 40/100, and fewer than 2 completed interviews "
    "recorded in the past 30 days. Score is the count of rules met out of 3, not a risk "
    "probability. Missing interview scores remain unknown. Recorded activity reflects "
    "available records and opportunities, not effort; verify context with a human. "
    "No trained model or real-world accuracy claim.")


def evaluate_support(student, skills, job, completed_count):
    gaps = [g for g in skill_gaps(skills, job.required_skills) if g["status"] != "on-track"]
    score = student.interview_score
    factors = [
        dict(key="skill_gaps", label="Technical support", value=len(gaps), threshold="3 or more role skill gaps",
            triggered=len(gaps) >= 3, contribution=int(len(gaps) >= 3),
            explanation=(f"{len(gaps)} gaps for {job.title}: " + (", ".join(f"{g['skill_name']} {g['proficiency']:g}/{g['required']:g}" for g in gaps) or "none")
                + ". Targets and proficiencies are proposed/self-reported.")),
        dict(key="interview", label="Interview preparation", value=score, threshold="Recorded interview score below 40/100",
            triggered=score is not None and score < 40, contribution=int(score is not None and score < 40),
            explanation="Interview score is missing; do not infer low performance." if score is None
                else f"Existing self-reported interview score is {score:g}/100; the proposed support threshold is below 40."),
        dict(key="activity", label="Recorded participation", value=completed_count, threshold="Fewer than 2 completed interviews in the past 30 days",
            triggered=completed_count < 2, contribution=int(completed_count < 2),
            explanation=f"{completed_count} completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records.")
    ]
    count = sum(f["contribution"] for f in factors)
    flagged = count == 3
    interventions = [
        dict(category="Technical", action="Offer focused practical training in " + ", ".join(g["skill_name"] for g in gaps) + "; review evidence after practice."),
        dict(category="Interview preparation", action="Arrange a mentor-led practice session and review the existing assessment; no automated mock-interview feature is used."),
        dict(category="Mentoring", action="Check whether suitable drives were available and attendance was recorded; agree on one achievable next participation step.")
    ] if flagged else []
    return SupportCalculation(score=count, support_priority="high" if flagged else "low", flagged=flagged,
        assessable=score is not None, contributing_factors=factors, recommendation=interventions,
        explanation=(f"{count}/3 support indicators meet the proposed thresholds. "
            + ("This student may benefit from technical, interview-preparation and mentoring support; an administrator should review the evidence and context."
                if flagged else "The combined support rule is not triggered; this is not a prediction of success or failure.")
            + (" The missing interview score needs clarification." if score is None else "")), methodology=METHOD)
