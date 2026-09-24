"""Trained public-data signal, separate from weighted readiness and recruitment rules.

Tree-path attribution sums to the individual's forest output. This is a descriptive
model decomposition, not causal evidence, global feature importance or SHAP.
"""
import hashlib
import json
import logging
from importlib.metadata import version
from pathlib import Path

from sqlalchemy import select, update
from models import PlacementModelProfile
from schemas import PlacementModelInput, PlacementModelResponse

DIRECTORY = Path(__file__).resolve().parents[1] / "ml"
LABELS = {
    "ssc_p": "10th percentage", "hsc_p": "12th percentage", "degree_p": "Degree percentage",
    "etest_p": "Employability test percentage", "mba_p": "MBA percentage", "gender": "Gender",
    "ssc_b": "10th board", "hsc_b": "12th board", "hsc_s": "12th stream",
    "degree_t": "Degree type", "workex": "Prior work experience", "specialisation": "MBA specialisation",
}
METHOD = ("Random Forest trained on public placement labels. Tree-path changes, averaged over 300 trees "
          "and grouped by input, add to the training-root baseline to explain the score. "
          "This is an uncalibrated model score out of 100, not a personal percentage chance or a causal effect.")
LIMITATIONS = [
    "Public Campus Recruitment dataset: 215 records; model fitted on 172, evaluated on 43 held-out records.",
    "Small anonymized MBA cohort; results have not been validated for another college or degree programme.",
    "Original collection is publisher-reported; the source test's measurement comparability is not established.",
    "Gender and educational background can encode bias; fairness and probability calibration are unverified.",
    "Optional informational signal only. It does not change readiness, matching, eligibility, offers or support flags.",
]
_pipeline = None
_report = None
_attempted = False


def load_model():
    """Load a trusted local artifact once per process, never train on startup/request."""
    global _pipeline, _report, _attempted
    if _attempted:
        return
    _attempted = True
    try:
        report = json.loads((DIRECTORY / "evaluation_report.json").read_text(encoding="utf-8"))
        artifact = DIRECTORY / "readiness_model.joblib"
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != report["artifact"]["sha256"]:
            raise ValueError("Model checksum mismatch")
        for package, key in (("scikit-learn", "scikit_learn"), ("numpy", "numpy"),
                             ("pandas", "pandas"), ("joblib", "joblib")):
            if version(package) != report["versions"][key]:
                raise ValueError("Model dependency version mismatch")
        import joblib
        pipeline = joblib.load(artifact)  # Never accept uploaded or remote pickle/joblib artifacts.
        if list(pipeline.named_steps["classifier"].classes_) != ["Not Placed", "Placed"]:
            raise ValueError("Unexpected class order")
        if list(pipeline.feature_names_in_) != report["feature_columns"]:
            raise ValueError("Unexpected feature schema")
        _pipeline, _report = pipeline, report
    except Exception as error:
        # Preserve the existing app when the optional model is unavailable; no fallback score.
        logging.getLogger("jobjugaad").error("Placement model unavailable (%s)", type(error).__name__)


def model_status():
    return "ready" if _pipeline is not None else ("unavailable" if _attempted else "not_loaded")


def evaluation():
    if _report is None:
        return None
    return {key: _report[key] for key in ("dataset_rows", "train_rows", "test_rows")} | {
        key: _report["metrics"][key] for key in ("accuracy", "precision", "recall", "f1")
    } | {"confusion_matrix": _report["confusion_matrix"]["values"],
         "source_url": _report["data_source"]["original_source"]}


def predict_signal(inputs: PlacementModelInput):
    values = inputs.model_dump()
    missing = [key for key, value in values.items() if value is None]
    result = {"available": False, "explanation": "The model is unavailable. Please try again later.",
              "missing_fields": missing, "methodology": METHOD, "limitations": LIMITATIONS}
    if missing:
        result["explanation"] = "No model score: provide recorded values for " + ", ".join(LABELS[k] for k in missing) + ". Do not invent missing academic records."
        return result
    if _pipeline is None:
        return result
    from engines.forest_explanation import describe_forest
    score, baseline, contributions = describe_forest(_pipeline, _report, values, LABELS)
    strongest = sorted(contributions, key=lambda key: abs(contributions[key]), reverse=True)[:2]
    reasons = "; ".join(f"{LABELS[key]} contributes {contributions[key]:+.2f} points" for key in strongest)
    return result | {"available": True, "score": score, "baseline": baseline,
        "breakdown": [{"key": key, "label": LABELS[key], "value": values[key], "contribution": contributions[key]} for key in LABELS],
        "explanation": f"The model score is {score:.2f}/100 from a {baseline:.2f}-point training baseline; {reasons}. This describes model behavior, not your probability of placement.",
        "model_version": _report["artifact"]["sha256"]}


def profile_response(session, student, payload=None):
    # Lock the owned parent to serialize concurrent saves of the optional one-to-one record.
    if payload is not None:
        from models import Student
        session.execute(select(Student.id).where(Student.id == student.id,
            Student.college_id == student.college_id).with_for_update()).scalar_one()
    row = session.scalar(select(PlacementModelProfile).where(
        PlacementModelProfile.student_id == student.id, PlacementModelProfile.college_id == student.college_id))
    if payload is not None:
        if row is None:
            row = PlacementModelProfile(student_id=student.id, college_id=student.college_id, inputs=payload.model_dump())
            session.add(row)
        else:
            session.execute(update(PlacementModelProfile).where(PlacementModelProfile.id == row.id,
                PlacementModelProfile.student_id == student.id, PlacementModelProfile.college_id == student.college_id)
                .values(inputs=payload.model_dump()))
        session.flush()
    inputs = payload if payload is not None else PlacementModelInput.model_validate(row.inputs if row else {})
    return PlacementModelResponse(inputs=inputs, signal=predict_signal(inputs), evaluation=evaluation())
