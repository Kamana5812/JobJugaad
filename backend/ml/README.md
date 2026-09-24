# Placement Likelihood Model — offline evaluation milestone

This is a separate **trained Random Forest placement-status classifier**, not the existing **Weighted Readiness Score**. The public Campus Recruitment dataset contains 215 labeled records; the fixed split trains on 172 and tests on 43. Do not describe the saved model as fitted on all 215. Dataset provenance and caveats are in [data/README.md](../data/README.md).

## Reproduce

From the repository root, with the pinned backend dependencies installed:

```powershell
backend/venv/Scripts/python.exe backend/ml/train_readiness_model.py
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
backend/venv/Scripts/python.exe -m unittest discover -s backend/tests -p test_public_placement_model.py -v
```

The trainer validates the source checksum, splits raw rows stratified by status using seed 42, fits categorical encoding on training rows only, and trains the predeclared 300-tree forest with balanced training class weights. It excludes sl_no, status and salary from all predictors. Structural salary nulls are never imputed. Model choices were recorded before the first training run in commit `cde4998`; no test-set tuning or seed search is permitted under this protocol.

`evaluation_report.json` records actual held-out metrics, both class reports, a confusion matrix with explicit label order, majority baseline, row IDs for reproducing the split, library versions and source/model hashes. `readiness_model.joblib` contains the same fitted preprocessing/classifier pipeline used for evaluation, not a refit on the holdout. The filename follows the user request; its target is observed placement status, not readiness bands. Load only this trusted, checksum-matching local artifact, with compatible pinned dependencies; joblib files can execute code and must not come from user uploads.

## Integration gate

The user requested the measured metrics before frontend integration. This milestone changes no API routes, database schema, startup loading, student profile inputs, frontend or deployed scoring. The next stage must load the saved artifact once at startup, never train per request, and keep the two outputs separate. Every model signal must have contributing factors and a plain-language explanation; global forest feature importance alone is not a per-student explanation.

Future inference needs the same 12 fields: ssc_p, hsc_p, degree_p, etest_p, mba_p, gender, ssc_b, hsc_b, hsc_s, degree_t, workex and specialisation. Do not manufacture MBA records, map CGPA to percentage without an institution's grading rule, or silently treat an unrelated aptitude score as the source test. Missing/incompatible inputs must produce an unavailable signal with a reason. Gender and educational-background predictors can encode bias; neither fairness nor transportability to engineering colleges has been established. A forest output is uncalibrated and must not be advertised as a validated personal probability or used for automatic rejection.

Matching/skill gaps/projects/certifications/resume and the 4,800-profile demo remain synthetic. Their frozen synthetic sanity checks are unchanged. The existing support-flag engine remains rule-based; this experiment is not an At-Risk classifier upgrade. If that separate upgrade is later requested, SMOTE or class weighting remains mandatory.

## Completed evaluation

The one fixed run achieved 38/43 correct: accuracy 88.37%, Placed precision 93.10%, recall 90.00%, F1 91.53%. [Measured results and confusion matrix](EVALUATION.md) include both classes and limitations. Five offline integrity/reproduction tests and the dependency check passed. No API/frontend integration or deployment occurred; the user metric-review gate remains in place.
