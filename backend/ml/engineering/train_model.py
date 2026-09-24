"""Train once on publisher-reported engineering placement labels; never imported by API."""
import hashlib
import json
import platform
from pathlib import Path
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.dummy import DummyClassifier

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "data" / "engineering" / "collegePlace.csv"
PROTOCOL = json.loads((HERE / "training_protocol.json").read_text(encoding="utf-8"))
FEATURES = PROTOCOL["features"]

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_dataset(path=DATA):
    if sha256(path) != PROTOCOL["dataset_sha256"]:
        raise ValueError("Engineering dataset checksum changed")
    data = pd.read_csv(path)
    if data.shape != (2966, 8) or set(data.columns) != set(FEATURES + PROTOCOL["excluded_columns"]):
        raise ValueError("Unexpected engineering source schema")
    if data.isna().any().any() or set(data.PlacedOrNot) != {0, 1}:
        raise ValueError("Missing source fields or unexpected labels")
    for key, low, high in [("CGPA",5,9),("Internships",0,3),("HistoryOfBacklogs",0,1)]:
        if not np.isfinite(data[key]).all() or not data[key].between(low,high).all() or not (data[key] % 1 == 0).all():
            raise ValueError("Unexpected recorded input range")
    return data

def split_dataset(data):
    # Group by ALL modeled input values, never by label; even conflicting-label
    # copies of the same input must stay together. No best-of-fold selection.
    groups = pd.factorize(pd.MultiIndex.from_frame(data[FEATURES]), sort=True)[0]
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train, test = next(splitter.split(data[FEATURES], data.PlacedOrNot, groups))
    assert not set(groups[train]) & set(groups[test])
    return train, test, groups

def build_pipeline():
    preprocess = ColumnTransformer([
        ("numeric", "passthrough", PROTOCOL["numeric_features"]),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), PROTOCOL["categorical_features"]),
    ], remainder="drop")
    # Fixed design assumptions. No holdout tuning; balance TRAINING classes only.
    return Pipeline([("preprocess",preprocess),("classifier",RandomForestClassifier(**PROTOCOL["random_forest"]))])

def main():
    data = load_dataset()
    train, test, groups = split_dataset(data)
    x_train, x_test = data.iloc[train][FEATURES], data.iloc[test][FEATURES]
    y_train, y_test = data.iloc[train].PlacedOrNot, data.iloc[test].PlacedOrNot
    model = build_pipeline().fit(x_train,y_train)
    predicted = model.predict(x_test)
    metrics = classification_report(y_test,predicted,labels=[0,1],output_dict=True,zero_division=0)
    baseline = DummyClassifier(strategy="most_frequent").fit(x_train,y_train)
    artifact = HERE / "placement_model.joblib"
    joblib.dump(model,artifact,compress=3)
    assert np.array_equal(joblib.load(artifact).predict(x_test),predicted)
    report = {"model_name":"BTech Placement Likelihood Model","model_type":"RandomForestClassifier",
        "evaluated_at":datetime.now(timezone.utc).isoformat(),"data_source":json.loads((DATA.parent/"source.json").read_text(encoding="utf-8")),
        "dataset_rows":len(data),"train_rows":len(train),"test_rows":len(test),
        "distinct_profiles":int(len(set(groups))),"train_groups":int(len(set(groups[train]))),"test_groups":int(len(set(groups[test]))),
        "group_overlap":0,"class_counts":{name:{str(label):int(frame.PlacedOrNot.eq(label).sum()) for label in (0,1)} for name,frame in [("full",data),("train",data.iloc[train]),("test",data.iloc[test])]},
        "feature_columns":FEATURES,"protocol":PROTOCOL,"protocol_sha256":sha256(HERE/"training_protocol.json"),
        "train_row_numbers":[int(i)+1 for i in train],"test_row_numbers":[int(i)+1 for i in test],
        "metrics":{"positive_class":"Placed (1)","accuracy":float(accuracy_score(y_test,predicted)),
            **{key:metrics["1"][key if key!="f1" else "f1-score"] for key in ("precision","recall","f1")},
            "per_class":{label:metrics[str(i)] for i,label in enumerate(["Not Placed","Placed"])}},
        "confusion_matrix":{"rows":"actual","columns":"predicted","label_order":["Not Placed","Placed"],"values":confusion_matrix(y_test,predicted,labels=[0,1]).tolist()},
        "most_frequent_baseline_accuracy":float(accuracy_score(y_test,baseline.predict(x_test))),
        "held_out_predictions":[{"row_number":int(i)+1,"actual":int(actual),"predicted":int(prediction)} for i,actual,prediction in zip(test,y_test,predicted)],
        "artifact":{"filename":artifact.name,"sha256":sha256(artifact),"trained_rows":len(train),"refit_on_all_data":False},
        "versions":{"python":platform.python_version(),"scikit_learn":sklearn.__version__,"pandas":pd.__version__,"numpy":np.__version__,"joblib":joblib.__version__},
        "limitations":["Publisher-reported university engineering records from 2013-2014; original collection is not independently audited.",
            "Only 181 distinct modeled profiles among 2966 rows; repeated/coarse inputs and mixed outcomes limit effective diversity.",
            "First fixed group-disjoint split, approximately 80/20; no external campus/temporal test or probability calibration.",
            "No age, gender or hostel predictors. This design choice does not establish fairness.",
            "CGPA through semester 6 and ever having backlogs are distinct from final CGPA and active backlog count.",
            "Optional experimental signal, never a placement guarantee, eligibility decision or replacement for weighted readiness."]}
    (HERE/"evaluation_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ("dataset_rows","train_rows","test_rows","distinct_profiles","train_groups","test_groups","class_counts","metrics","confusion_matrix","most_frequent_baseline_accuracy")},indent=2))

if __name__ == "__main__":
    main()
