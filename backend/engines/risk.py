import os
import joblib
import pandas as pd
from engines.skill_gap import skill_gaps
from schemas import SupportCalculation

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "support_model.joblib")
try:
    support_model = joblib.load(MODEL_PATH)
    METHOD = ("Machine Learning Classifier (Random Forest) trained with balanced class weights. "
              "Factors derived from feature importances based on skill gaps, interview score, and activity. "
              "Not a guarantee of placement failure, but a priority indicator.")
except Exception:
    support_model = None
    METHOD = ("Proposed deterministic AND rule: at least 3 skill gaps for the selected role, "
        "a recorded interview score below 40/100, and fewer than 2 completed interviews "
        "recorded in the past 30 days. Score is the count of rules met out of 3, not a risk "
        "probability. Missing interview scores remain unknown. Recorded activity reflects "
        "available records and opportunities, not effort; verify context with a human. "
        "No trained model or real-world accuracy claim.")

def evaluate_support(student, skills, job, completed_count):
    gaps = [g for g in skill_gaps(skills, job.required_skills) if g["status"] != "on-track"]
    num_gaps = len(gaps)
    score_val = student.interview_score
    interview_score = score_val if score_val is not None else 50.0

    if support_model:
        # Use ML Model
        X = pd.DataFrame([{
            'num_skill_gaps': num_gaps,
            'interview_score': interview_score,
            'recent_activity': completed_count
        }])
        prob = support_model.predict_proba(X)[0][1]
        score = int(prob * 100)
        flagged = prob >= 0.5
        
        factors = [
            dict(key="skill_gaps", label="Technical support", value=num_gaps, threshold="Model identified high importance",
                triggered=num_gaps > 0, contribution=int(support_model.feature_importances_[0]*100),
                explanation=f"{num_gaps} gaps for {job.title}." + ("" if num_gaps == 0 else f" (Impact weight: {support_model.feature_importances_[0]:.2f})")),
            dict(key="interview", label="Interview preparation", value=interview_score, threshold="Model threshold consideration",
                triggered=score_val is not None and score_val < 50, contribution=int(support_model.feature_importances_[1]*100),
                explanation="Score is imputed as 50.0 due to missing data." if score_val is None else f"Reported score {score_val:g}/100. (Impact weight: {support_model.feature_importances_[1]:.2f})"),
            dict(key="activity", label="Recorded participation", value=completed_count, threshold="Model activity threshold",
                triggered=completed_count < 2, contribution=int(support_model.feature_importances_[2]*100),
                explanation=f"{completed_count} recent interviews. (Impact weight: {support_model.feature_importances_[2]:.2f})")
        ]
        
        interventions = [
            dict(category="Technical", action="Offer focused practical training in missing skills; review evidence after practice."),
            dict(category="Interview preparation", action="Arrange a mentor-led practice session to improve scores."),
            dict(category="Mentoring", action="Assign a mentor to track application activity and interview attendance.")
        ] if flagged else []
        
        return SupportCalculation(
            score=score, 
            score_label="Predicted Support Probability (%)",
            support_priority="high" if flagged else "low", 
            flagged=flagged,
            assessable=score_val is not None, 
            contributing_factors=factors, 
            recommendation=interventions,
            explanation=f"The Machine Learning model estimates a {score}% likelihood that additional placement support is needed based on the feature profile.", 
            methodology=METHOD
        )
    else:
        # Fallback to rules
        factors = [
            dict(key="skill_gaps", label="Technical support", value=len(gaps), threshold="3 or more role skill gaps",
                triggered=len(gaps) >= 3, contribution=int(len(gaps) >= 3),
                explanation=(f"{len(gaps)} gaps for {job.title}: " + (", ".join(f"{g['skill_name']} {g['proficiency']:g}/{g['required']:g}" for g in gaps) or "none")
                    + ". Targets and proficiencies are proposed/self-reported.")),
            dict(key="interview", label="Interview preparation", value=score_val, threshold="Recorded interview score below 40/100",
                triggered=score_val is not None and score_val < 40, contribution=int(score_val is not None and score_val < 40),
                explanation="Interview score is missing; do not infer low performance." if score_val is None
                    else f"Existing self-reported interview score is {score_val:g}/100; the proposed support threshold is below 40."),
            dict(key="activity", label="Recorded participation", value=completed_count, threshold="Fewer than 2 completed interviews in the past 30 days",
                triggered=completed_count < 2, contribution=int(completed_count < 2),
                explanation=f"{completed_count} completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records.")
        ]
        sources = getattr(student, '_assessment_sources', {})
        if 'interview' in sources:
            factors[1]['explanation'] = sources['interview'] + ' Proposed support threshold: below 40/100.'
        skill_sources = [source for key, source in sources.items() if key.startswith('skill:')]
        if skill_sources:
            factors[0]['explanation'] += ' Adopted skill evidence: ' + ' '.join(skill_sources)
        count = sum(f["contribution"] for f in factors)
        flagged = count == 3
        interventions = [
            dict(category="Technical", action="Offer focused practical training in " + ", ".join(g["skill_name"] for g in gaps) + "; review evidence after practice."),
            dict(category="Interview preparation", action="Arrange a mentor-led practice session and review the existing assessment; no automated mock-interview feature is used."),
            dict(category="Mentoring", action="Check whether suitable drives were available and attendance was recorded; agree on one achievable next participation step.")
        ] if flagged else []
        return SupportCalculation(
            score=count, 
            score_label="Support indicators met /3",
            support_priority="high" if flagged else "low", 
            flagged=flagged,
            assessable=score_val is not None, 
            contributing_factors=factors, 
            recommendation=interventions,
            explanation=(f"{count}/3 support indicators meet the proposed thresholds. "
                + ("This student may benefit from technical, interview-preparation and mentoring support; an administrator should review the evidence and context."
                    if flagged else "The combined support rule is not triggered; this is not a prediction of success or failure.")
                + (" The missing interview score needs clarification." if score_val is None else "")), methodology=METHOD)

