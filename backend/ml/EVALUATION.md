# Public placement classifier — measured held-out results

Evaluation timestamp: 2026-09-24T00:53:29.654286+00:00. Source/protocol/trainer frozen before execution in commit **cde4998**. This is a measured evaluation on imported public Campus Recruitment labels, **not** a synthetic sanity check. Original data collection is publisher-reported; no independent authenticity audit is claimed.

Accuracy **88.37%**, precision **93.10%**, recall **90.00%**, F1 **91.53%** (positive class: Placed; **43 held-out records**, 172 training, 215 total).

| Metric | Observed result |
|---|---:|
| Correct test predictions | 38 / 43 |
| Accuracy | 88.37% |
| Precision — Placed | 93.10% |
| Recall — Placed | 90.00% |
| F1 — Placed | 91.53% |
| Precision — Not Placed | 78.57% |
| Recall — Not Placed | 84.62% |
| F1 — Not Placed | 81.48% |
| Always predict the training majority class: test accuracy | 69.77% |

Rows are **actual**, columns are **predicted**:

| Actual \ Predicted | Not Placed | Placed |
|---|---:|---:|
| Not Placed | 11 | 2 |
| Placed | 3 | 27 |

Two unplaced records were predicted Placed; three placed records were predicted Not Placed. The held-out set contains 13 Not Placed and 30 Placed records. Both classes are reported rather than only the majority class.

## Protocol and reproducibility

The original file has 148 Placed / 67 Not Placed records. Split: stratified 80/20, random seed 42, training class counts 118/54 and test counts 30/13 (Placed/Not Placed). One-hot encoding was fit on training rows only. All 12 predictors remaining after dropping sl_no, status and salary were used; salary's 67 structural nulls were retained in the CSV and excluded from the model. No synthetic records or labels were added. The fixed 300-tree Random Forest uses min_samples_leaf=2 and balanced training class weights, without test tuning, threshold search or holdout refitting.

The saved pipeline is the exact model fit on **172** rows and evaluated on **43**—not a model fit on all 215. [Full report](evaluation_report.json) includes predictions, split row IDs, settings, versions and checksums. [Training script](train_readiness_model.py), [protocol](training_protocol.json), [source](../data/source.json) and [reproduction instructions](README.md) are retained. No comparative Random Forest superiority claim or unverified research benchmark is made.

## Interpretation and limits

There are only 215 total records and 43 test cases: changing one test prediction changes accuracy by about 2.33 percentage points. This is one internal random split from an anonymized MBA-oriented campus, with no independent, temporal or BPUT-college test. It is not production-grade accuracy or a calibrated personal placement probability. Gender/education features may encode historical bias; fairness and causal effects have not been established. All listed fields, including MBA evidence, must be compatible before any later inference; engineering CGPA or unrelated tests must not be silently substituted.

The existing 30/20/15/15/10/10 Weighted Readiness Score is unchanged and not validated by these results. Matching/skill gaps/projects/certifications/resumes and the 4,800-profile workflow demo remain synthetic; their frozen matching/scoring sanity checks are untouched. The support-flag engine remains rule-based. This model is **offline only**, awaiting the user's metric review before API/frontend integration. Any later per-student signal must include factor contributions and a plain-language explanation and must stay distinct from weighted readiness.
