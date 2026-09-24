"""Train a separate placement classifier on imported public labels, not readiness rules.

Run: backend/venv/Scripts/python.exe backend/ml/train_readiness_model.py
The filename follows the user request; the target is placement status, NOT the
weighted readiness score. No API startup or request imports/runs this trainer.
"""
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "Placement_Data_Full_Class.csv"
PROTOCOL = json.loads((HERE / "training_protocol.json").read_text(encoding="utf-8"))
LABELS = ["Not Placed", "Placed"]
NUMERIC = PROTOCOL["numeric_features"]
CATEGORICAL = PROTOCOL["categorical_features"]
EXCLUDED = PROTOCOL["excluded_columns"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dataset(path=DATA):
    if sha256(path) != PROTOCOL["dataset_sha256"]:
        raise ValueError("Dataset checksum changed; review provenance and protocol before training.")
    data = pd.read_csv(path)
    expected = set(NUMERIC + CATEGORICAL + EXCLUDED)
    if data.shape != (215, 15) or set(data.columns) != expected:
        raise ValueError("Expected the pinned 215-row, 15-column Campus Recruitment file.")
    if data["sl_no"].isna().any() or not data["sl_no"].is_unique:
        raise ValueError("Row identifiers must be non-null and unique.")
    if set(data["status"]) != set(LABELS):
        raise ValueError("Unexpected placement labels.")
    # Salary is an outcome: structural nulls are left untouched, never imputed.
    if not data["salary"].isna().equals(data["status"].eq("Not Placed")):
        raise ValueError("Salary nulls do not match the documented structural pattern.")
    features = data.drop(columns=EXCLUDED)
    if features.isna().any().any():
        raise ValueError("Predictor values are missing; do not silently invent academic evidence.")
    for column in NUMERIC:
        values = pd.to_numeric(features[column], errors="raise")
        if not np.isfinite(values).all() or not values.between(0, 100).all():
            raise ValueError(f"{column} must contain finite percentages between 0 and 100.")
    if any(not features[column].map(lambda value: isinstance(value, str) and bool(value.strip())).all()
           for column in CATEGORICAL):
        raise ValueError("Categorical predictors must be nonempty strings.")
    if features.duplicated().any():
        raise ValueError("Duplicate predictor rows need a grouped-split review before evaluation.")
    return data


def split_dataset(data):
    # Split raw rows before fitting any categorical preprocessing.
    train, test = train_test_split(data, test_size=PROTOCOL["split"]["test_size"],
        random_state=PROTOCOL["split"]["random_state"], shuffle=True, stratify=data["status"])
    return train, test


def build_pipeline():
    preprocessing = ColumnTransformer([
        ("numeric", "passthrough", NUMERIC),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
    ], remainder="drop")
    # Fixed predeclared assumptions, not empirically tuned against the holdout.
    # Balanced class weights are learned from TRAINING labels only; no SMOTE/test resampling.
    return Pipeline([("preprocess", preprocessing),
                     ("classifier", RandomForestClassifier(**PROTOCOL["random_forest"]))])


def class_counts(frame):
    return {label: int(frame["status"].eq(label).sum()) for label in LABELS}


def train_and_evaluate(output_dir=HERE):
    data = load_dataset()
    train, test = split_dataset(data)
    x_train, x_test = train.drop(columns=EXCLUDED), test.drop(columns=EXCLUDED)
    y_train, y_test = train["status"], test["status"]
    model = build_pipeline().fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics = classification_report(y_test, predictions, labels=LABELS, output_dict=True, zero_division=0)
    baseline = DummyClassifier(strategy="most_frequent").fit(x_train, y_train)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / "readiness_model.joblib"
    joblib.dump(model, artifact, compress=3)
    # Loading is safe here only because this process just created the local artifact.
    reloaded = joblib.load(artifact)
    if not np.array_equal(reloaded.predict(x_test), predictions):
        raise RuntimeError("Saved model failed prediction round-trip verification.")
    source = json.loads((DATA.parent / "source.json").read_text(encoding="utf-8"))
    report = {
        "model_name": "Placement Likelihood Model",
        "model_type": "RandomForestClassifier",
        "target": "Observed public placement status; separate from Weighted Readiness Score",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": source,
        "dataset_rows": len(data), "train_rows": len(train), "test_rows": len(test),
        "class_counts": {"full": class_counts(data), "train": class_counts(train), "test": class_counts(test)},
        "protocol": PROTOCOL,
        "protocol_sha256": sha256(HERE / "training_protocol.json"),
        "feature_columns": list(x_train.columns),
        "excluded_columns": EXCLUDED,
        "structural_salary_nulls": int(data["salary"].isna().sum()),
        "train_sl_no": [int(value) for value in train["sl_no"]],
        "test_sl_no": [int(value) for value in test["sl_no"]],
        "metrics": {"positive_class": "Placed", "accuracy": float(accuracy_score(y_test, predictions)),
                    "precision": metrics["Placed"]["precision"], "recall": metrics["Placed"]["recall"],
                    "f1": metrics["Placed"]["f1-score"], "per_class": {label: metrics[label] for label in LABELS},
                    "macro_average": metrics["macro avg"], "weighted_average": metrics["weighted avg"]},
        "confusion_matrix": {"rows": "actual", "columns": "predicted", "label_order": LABELS,
                             "values": confusion_matrix(y_test, predictions, labels=LABELS).tolist()},
        "most_frequent_baseline_accuracy": float(accuracy_score(y_test, baseline.predict(x_test))),
        "held_out_predictions": [{"sl_no": int(identity), "actual": actual, "predicted": predicted}
            for identity, actual, predicted in zip(test["sl_no"], y_test, predictions)],
        "artifact": {"filename": artifact.name, "sha256": sha256(artifact), "trained_rows": len(train),
                     "refit_on_all_data": False, "trusted_local_artifacts_only": True},
        "versions": {"python": platform.python_version(), "pandas": pd.__version__,
                     "scikit_learn": sklearn.__version__, "joblib": joblib.__version__, "numpy": np.__version__},
        "interpretation": "Measured held-out results on imported public labels, not a synthetic sanity check. "
                          "They do not establish performance at a different college or production-grade accuracy.",
        "limitations": [
            "Only 215 records from an anonymized MBA-oriented campus; 43 test records and no external validation.",
            "One fixed stratified split; no cross-validation, confidence calibration, temporal or campus holdout.",
            "Original data collection/authenticity is publisher-reported and has not been independently audited.",
            "Gender and education-background predictors can encode historical bias; fairness is not established.",
            "MBA percentages/specialisation and other compatible fields are required; no invented values or CGPA conversion.",
            "Forest probabilities are uncalibrated scores, not validated individual placement likelihoods.",
            "This artifact is not connected to student decisions, matching, support flags, the API or the frontend.",
        ],
    }
    (output_dir / "evaluation_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    report = train_and_evaluate()
    print(f"Public dataset n={report['dataset_rows']}; train={report['train_rows']}; held-out test={report['test_rows']}")
    print("Positive class: Placed. One fixed stratified 80/20 split; no test-set tuning.")
    for metric in ("accuracy", "precision", "recall", "f1"):
        print(f"{metric}: {report['metrics'][metric]:.6f} ({report['metrics'][metric]:.2%})")
    print("Confusion matrix: rows actual / columns predicted; order [Not Placed, Placed]")
    print(np.array(report["confusion_matrix"]["values"]))
    print("Per-class metrics:", json.dumps(report["metrics"]["per_class"]))
    print(f"Majority-class baseline accuracy: {report['most_frequent_baseline_accuracy']:.2%}")
    print(report["interpretation"])
    print("Model and report saved. API/frontend integration awaits user metric review.")


if __name__ == "__main__":
    main()
