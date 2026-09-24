"""Offline model integrity tests; no database, live accounts or synthetic labels."""
import json
import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, f1_score
from ml.train_readiness_model import DATA, HERE, PROTOCOL, LABELS, EXCLUDED, CATEGORICAL, load_dataset, split_dataset, sha256


class PublicPlacementModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_dataset()
        cls.train, cls.test = split_dataset(cls.data)
        cls.report = json.loads((HERE / "evaluation_report.json").read_text(encoding="utf-8"))
        artifact = HERE / "readiness_model.joblib"
        if sha256(artifact) != cls.report["artifact"]["sha256"]:
            raise RuntimeError("Artifact does not match the recorded trusted training run.")
        cls.model = joblib.load(artifact)

    def test_source_integrity_and_structural_salary(self):
        self.assertEqual(self.data.shape, (215, 15))
        self.assertEqual(sha256(DATA), self.report["data_source"]["sha256"])
        self.assertEqual(self.data["status"].value_counts().to_dict(), {"Placed": 148, "Not Placed": 67})
        self.assertEqual(int(self.data["salary"].isna().sum()), 67)
        self.assertTrue(self.data["salary"].isna().equals(self.data["status"].eq("Not Placed")))

    def test_stratified_disjoint_reproducible_split(self):
        train_ids, test_ids = set(self.train.sl_no), set(self.test.sl_no)
        self.assertEqual((len(train_ids), len(test_ids)), (172, 43))
        self.assertFalse(train_ids & test_ids)
        self.assertEqual(train_ids | test_ids, set(self.data.sl_no))
        self.assertEqual(self.test["status"].value_counts().to_dict(), {"Placed": 30, "Not Placed": 13})
        self.assertEqual(list(self.test.sl_no), self.report["test_sl_no"])
        self.assertEqual(list(self.train.sl_no), self.report["train_sl_no"])
        self.assertFalse(self.report["artifact"]["refit_on_all_data"])

    def test_no_identifier_salary_label_or_synthetic_features(self):
        features = list(self.model.feature_names_in_)
        self.assertEqual(set(features), set(PROTOCOL["numeric_features"] + CATEGORICAL))
        self.assertFalse(set(features) & set(EXCLUDED))
        self.assertEqual(features, self.report["feature_columns"])
        self.assertEqual(self.model.named_steps["classifier"].class_weight, "balanced")
        self.assertEqual(self.model.named_steps["preprocess"].remainder, "drop")
        encoder = self.model.named_steps["preprocess"].named_transformers_["categorical"]
        for column, categories in zip(CATEGORICAL, encoder.categories_):
            self.assertEqual(set(categories), set(self.train[column]))
        original = self.test.drop(columns=EXCLUDED)
        changed = original.copy()
        changed[CATEGORICAL[0]] = "holdout-only-unseen-category"
        before = [list(values) for values in encoder.categories_]
        self.model.predict(changed)
        self.assertEqual(before, [list(values) for values in encoder.categories_])

    def test_saved_artifact_reproduces_reported_metrics_and_predictions(self):
        actual = self.test["status"]
        predicted = self.model.predict(self.test.drop(columns=EXCLUDED))
        self.assertEqual(confusion_matrix(actual, predicted, labels=LABELS).tolist(), self.report["confusion_matrix"]["values"])
        computed = {"accuracy": accuracy_score(actual, predicted),
            "precision": precision_score(actual, predicted, pos_label="Placed"),
            "recall": recall_score(actual, predicted, pos_label="Placed"),
            "f1": f1_score(actual, predicted, pos_label="Placed")}
        for name, value in computed.items():
            self.assertAlmostEqual(value, self.report["metrics"][name], places=12)
        self.assertEqual(list(predicted), [p["predicted"] for p in self.report["held_out_predictions"]])
        self.assertEqual(sha256(HERE / "training_protocol.json"), self.report["protocol_sha256"])

    def test_modified_dataset_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            modified = Path(directory) / DATA.name
            modified.write_bytes(DATA.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_dataset(modified)


if __name__ == "__main__":
    unittest.main()
