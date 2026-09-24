"""Exact original-field tree-path attribution, not causality or SHAP."""

def describe_forest(pipeline, report, values, labels):
    import numpy as np
    import pandas as pd
    frame = pd.DataFrame([values], columns=report["feature_columns"])
    preprocessing = pipeline.named_steps["preprocess"]
    forest = pipeline.named_steps["classifier"]
    # sklearn's trees traverse float32 inputs; use the identical representation.
    row = preprocessing.transform(frame).astype(np.float32)[0]
    numeric = report["protocol"]["numeric_features"]
    categorical = report["protocol"]["categorical_features"]
    encoder = preprocessing.named_transformers_["categorical"]
    feature_keys = list(numeric)
    for key, categories in zip(categorical, encoder.categories_):
        feature_keys.extend([key] * len(categories))
    contributions = dict.fromkeys(labels, 0.0)
    baseline = 0.0
    for estimator in forest.estimators_:
        tree = estimator.tree_
        # Handles either normalized probabilities or counts in tree.value.
        probabilities = tree.value[:, 0, 1] / tree.value[:, 0, :].sum(axis=1)
        baseline += float(probabilities[0])
        node = 0
        while tree.children_left[node] != tree.children_right[node]:
            feature = tree.feature[node]
            child = tree.children_left[node] if row[feature] <= tree.threshold[node] else tree.children_right[node]
            contributions[feature_keys[feature]] += float(probabilities[child] - probabilities[node])
            node = child
    scale = 100 / len(forest.estimators_)
    baseline *= scale
    contributions = {key: value * scale for key, value in contributions.items()}
    score = float(pipeline.predict_proba(frame)[0, 1] * 100)
    if abs(baseline + sum(contributions.values()) - score) > 1e-8:
        raise RuntimeError("Model explanation does not reconcile with prediction")
    return score, baseline, contributions
