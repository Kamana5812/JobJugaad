"""Optional engineering public-data model; never used to reject or rank candidates."""
import hashlib
import json
import logging
from importlib.metadata import version
from pathlib import Path
from sqlalchemy import select, update
from models import BTechModelProfile, Student
from schemas import BTechModelInput, BTechModelResponse
from engines.forest_explanation import describe_forest

DIRECTORY = Path(__file__).resolve().parents[1] / "ml" / "engineering"
KEYS = {"cgpa":"CGPA", "stream":"Stream", "internships":"Internships", "history_of_backlogs":"HistoryOfBacklogs"}
LABELS = {"CGPA":"CGPA through semester 6", "Stream":"Engineering stream", "Internships":"Completed internships", "HistoryOfBacklogs":"Ever had a backlog (1 yes, 0 no)"}
METHOD = ("Random Forest trained on public engineering-placement labels. A training-root baseline plus "
          "four signed tree-path contributions explains the uncalibrated model score out of 100. "
          "It is not a personal percentage chance, a causal effect or a readiness band.")
LIMITATIONS = [
    "Publisher-reported engineering records from 2013-2014; original collection is not independently audited.",
    "Only 181 distinct four-field profiles among 2,966 rows. Identical modeled inputs stay in the same evaluation split.",
    "No external college or recent-cohort validation, probability calibration or established fairness.",
    "The source covers six streams, CGPA 5-9 and 0-3 internships. Finer CGPA precision was not present in the source.",
    "Age, gender and hostel residence are excluded. MBA results are not required.",
    "Optional information only; no effect on weighted readiness, matching, eligibility, offers or support flags.",
]
_pipeline = None
_report = None
_attempted = False


def load_model():
    global _pipeline, _report, _attempted
    if _attempted:
        return
    _attempted = True
    try:
        report = json.loads((DIRECTORY / "evaluation_report.json").read_text(encoding="utf-8"))
        artifact = DIRECTORY / "placement_model.joblib"
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != report["artifact"]["sha256"]:
            raise ValueError("BTech model checksum mismatch")
        for package,key in (("scikit-learn","scikit_learn"),("numpy","numpy"),("pandas","pandas"),("joblib","joblib")):
            if version(package) != report["versions"][key]:
                raise ValueError("BTech dependency version mismatch")
        import joblib
        pipeline = joblib.load(artifact)  # Own trusted local artifact only, never uploads.
        if list(pipeline.named_steps["classifier"].classes_) != [0,1] or list(pipeline.feature_names_in_) != report["feature_columns"]:
            raise ValueError("Unexpected BTech artifact schema")
        _pipeline, _report = pipeline, report
    except Exception as error:
        logging.getLogger("jobjugaad").error("BTech model unavailable (%s)",type(error).__name__)


def model_status():
    return "ready" if _pipeline is not None else ("unavailable" if _attempted else "not_loaded")


def evaluation():
    if _report is None:
        return None
    return {key:_report[key] for key in ("dataset_rows","train_rows","test_rows","distinct_profiles","train_groups","test_groups")} | {
        key:_report["metrics"][key] for key in ("accuracy","precision","recall","f1")
    } | {"confusion_matrix":_report["confusion_matrix"]["values"], "source_url":_report["data_source"]["source_url"],
         "baseline_accuracy":_report["most_frequent_baseline_accuracy"]}


def predict_signal(inputs):
    values = {KEYS[key]:value for key,value in inputs.model_dump().items()}
    missing = [key for key,value in values.items() if value is None]
    result = {"available":False,"explanation":"The BTech model is unavailable. Please try again later.",
        "missing_fields":missing,"methodology":METHOD,"limitations":LIMITATIONS}
    if missing:
        result["explanation"] = "No BTech model score: provide recorded values for " + ", ".join(LABELS[key] for key in missing) + ". MBA details are not needed."
        return result
    outside = []
    if not 5 <= values["CGPA"] <= 9:
        outside.append("semester-6 CGPA outside the source range of 5-9")
    if values["Internships"] > 3:
        outside.append("internship count outside the source range of 0-3")
    if outside:
        result["explanation"] = "No BTech model score: " + "; ".join(outside) + ". Your evidence is saved unchanged; no value is capped or invented."
        return result
    if _pipeline is None:
        return result
    score, baseline, contributions = describe_forest(_pipeline,_report,values,LABELS)
    strongest = sorted(contributions,key=lambda key:abs(contributions[key]),reverse=True)[:2]
    reasons = "; ".join(f"{LABELS[key]} contributes {contributions[key]:+.2f} points" for key in strongest)
    return result | {"available":True,"score":score,"baseline":baseline,
        "breakdown":[{"key":key,"label":LABELS[key],"value":values[key],"contribution":contributions[key]} for key in LABELS],
        "explanation":f"The BTech model score is {score:.2f}/100 from a {baseline:.2f}-point training baseline; {reasons}. This describes model behavior, not your probability of placement.",
        "model_version":_report["artifact"]["sha256"]}


def profile_response(session,student,payload=None):
    if payload is not None:
        session.execute(select(Student.id).where(Student.id==student.id,Student.college_id==student.college_id).with_for_update()).scalar_one()
    row = session.scalar(select(BTechModelProfile).where(BTechModelProfile.student_id==student.id,BTechModelProfile.college_id==student.college_id))
    if payload is not None:
        if row is None:
            session.add(BTechModelProfile(student_id=student.id,college_id=student.college_id,inputs=payload.model_dump()))
        else:
            session.execute(update(BTechModelProfile).where(BTechModelProfile.id==row.id,BTechModelProfile.student_id==student.id,
                BTechModelProfile.college_id==student.college_id).values(inputs=payload.model_dump()))
        session.flush()
    inputs = payload if payload is not None else BTechModelInput.model_validate(row.inputs if row else {})
    return BTechModelResponse(inputs=inputs,signal=predict_signal(inputs),evaluation=evaluation())
