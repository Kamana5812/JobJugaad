# Phase 4 synthetic evaluation

**Assistant-authored synthetic sanity check against our own assumptions — not validated accuracy or independent human validation.**

Observed at 2026-09-23T03:48:55.305709+00:00. Frozen expectations: commit c2748bf, backend/evaluation_expected.json.

Matching reproduced **25 of 30 expected matches** across ten profiles. The engine returned 30 eligible slots. Synthetic micro precision: 25/30; recall: 25/30. These are self-labeled sanity-check fractions, not real-world accuracy.

Face-validity review agreed on **10 of 10 readiness bands** and **10 of 10 support flags**. The same ten profiles were used for both reviews.

## Per-profile matching comparison

| Seed | Expected top three | Actual top three | Reproduced |
|---|---|---|---|
| 301 | Simulated React Product Engineer; Simulated Web UI Developer; Simulated React Frontend Engineer | Simulated React Frontend Engineer; Simulated Web UI Developer; Simulated Web Apprentice | 2/3 |
| 302 | Simulated Java Platform Engineer; Simulated Java Graduate Engineer; Simulated Quality Automation Associate | Simulated Java Graduate Engineer; Simulated General Support Trainee; Simulated Java Platform Engineer | 2/3 |
| 303 | Simulated Python Cloud Engineer; Simulated Data Engineering Associate; Simulated Cloud Support Track | Simulated Cloud Support Track; Simulated Python Cloud Engineer; Simulated Data Engineering Associate | 3/3 |
| 304 | Simulated React Product Engineer; Simulated Web UI Developer; Simulated React Frontend Engineer | Simulated React Frontend Engineer; Simulated React Product Engineer; Simulated Web UI Developer | 3/3 |
| 306 | Simulated Cloud Support Track; Simulated Backend Apprentice; Simulated General Support Trainee | Simulated Backend Apprentice; Simulated Cloud Support Track; Simulated General Support Trainee | 3/3 |
| 307 | Simulated Web UI Developer; Simulated Web Apprentice; Simulated React Product Engineer | Simulated Web Apprentice; Simulated Web UI Developer; Simulated React Product Engineer | 3/3 |
| 313 | Simulated Web Apprentice; Simulated General Support Trainee; Simulated Backend Apprentice | Simulated Web Apprentice; Simulated Web UI Developer; Simulated General Support Trainee | 2/3 |
| 315 | Simulated Backend Apprentice; Simulated Cloud Support Track; Simulated General Support Trainee | Simulated Backend Apprentice; Simulated Cloud Support Track; Simulated General Support Trainee | 3/3 |
| 318 | Simulated Python Backend Engineer; Simulated Cloud Support Track; Simulated Data Engineering Associate | Simulated Python Cloud Engineer; Simulated Python Backend Engineer; Simulated Backend Apprentice | 1/3 |
| 320 | Simulated Java Graduate Engineer; Simulated Quality Automation Associate; Simulated General Support Trainee | Simulated General Support Trainee; Simulated Java Graduate Engineer; Simulated Quality Automation Associate | 3/3 |

## Mismatches and observations

- Seed 301: missed Simulated React Product Engineer. Returned instead: Simulated Web Apprentice.
  - Simulated React Product Engineer: Eligible, but outranked under the current requirement-coverage weights.
- Seed 302: missed Simulated Quality Automation Associate. Returned instead: Simulated General Support Trainee.
  - Simulated Quality Automation Associate: Eligible, but outranked under the current requirement-coverage weights.
- Seed 313: missed Simulated Backend Apprentice. Returned instead: Simulated Web UI Developer.
  - Simulated Backend Apprentice: Eligible, but outranked under the current requirement-coverage weights.
- Seed 318: missed Simulated Cloud Support Track; Simulated Data Engineering Associate. Returned instead: Simulated Python Cloud Engineer; Simulated Backend Apprentice.
  - Simulated Cloud Support Track: Eligible, but outranked under the current requirement-coverage weights.
  - Simulated Data Engineering Associate: Eligible, but outranked under the current requirement-coverage weights.

The reviewer favored role specialization and appropriate level. The formula rewards meeting listed targets and exact project keywords; lower-target apprentice roles can therefore outrank specialist roles. Equal scores use the frozen catalog order. These are inspectable limitations, not reasons to silently alter the expected labels or tune the result.

## Readiness and support face-validity review

| Seed | Expected readiness | Actual readiness | Expected support flag | Actual flag | Review result |
|---|---|---|---|---|---|
| 301 | Ready | Ready | False | False | Agrees |
| 302 | Ready | Ready | False | False | Agrees |
| 303 | Ready | Ready | False | False | Agrees |
| 304 | Highly Employable | Highly Employable | False | False | Agrees |
| 306 | Developing | Developing | False | False | Agrees |
| 307 | Developing | Developing | False | False | Agrees |
| 313 | Developing | Developing | True | True | Agrees |
| 315 | Developing | Developing | False | False | Agrees |
| 318 | Developing | Developing | False | False | Agrees |
| 320 | Developing | Developing | False | False | Agrees |

### Seed 301

Pre-run judgment: Strong React/CSS and three relevant projects support frontend roles; assessments are solid rather than uniformly exceptional. Cloud gaps alone do not trigger support because interview performance and activity are adequate.

Readiness: **75/100, Ready**. Your recorded profile totals 75/100 (Ready) under this weighted rule; academics is your strongest recorded factor and communication is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 74.11 | 30 | 22.23 | Mean of 5 self-reported skill proficiencies. |
| Projects | 75.0 | 20 | 15.0 | 3 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 79.0 | 15 | 11.85 | CGPA 7.9/10 x 10. |
| Aptitude | 74.52 | 15 | 11.18 | Self-reported existing assessment: 74.52/100. |
| Communication | 70.06 | 10 | 7.01 | Self-reported existing assessment: 70.06/100. |
| Interview | 72.76 | 10 | 7.28 | Self-reported existing assessment: 72.76/100. |

Support: **1/3 indicators**, flag **False** for Simulated Cloud Support Track. 1/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 3.0 | 3 or more role skill gaps | 1 | 3 gaps for Simulated Cloud Support Track: python 0/60, sql 0/60, aws 0/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 72.76 | Recorded interview score below 40/100 | 0 | Existing self-reported interview score is 72.76/100; the proposed support threshold is below 40. |
| Recorded participation | 3.0 | Fewer than 2 completed interviews in the past 30 days | 0 | 3 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 302

Pre-run judgment: Java is the strongest skill, with SQL/git projects and strong academics. The lower assessment results keep the overall view below the highest readiness band. Interview score and activity do not meet the support trigger.

Readiness: **77/100, Ready**. Your recorded profile totals 77/100 (Ready) under this weighted rule; projects is your strongest recorded factor and interview is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 73.71 | 30 | 22.11 | Mean of 4 self-reported skill proficiencies. |
| Projects | 100.0 | 20 | 20.0 | 4 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 89.5 | 15 | 13.43 | CGPA 8.95/10 x 10. |
| Aptitude | 61.61 | 15 | 9.24 | Self-reported existing assessment: 61.61/100. |
| Communication | 65.07 | 10 | 6.51 | Self-reported existing assessment: 65.07/100. |
| Interview | 58.39 | 10 | 5.84 | Self-reported existing assessment: 58.39/100. |

Support: **1/3 indicators**, flag **False** for Simulated Cloud Support Track. 1/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 3.0 | 3 or more role skill gaps | 1 | 3 gaps for Simulated Cloud Support Track: python 0/60, sql 55.57/60, aws 0/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 58.39 | Recorded interview score below 40/100 | 0 | Existing self-reported interview score is 58.39/100; the proposed support threshold is below 40. |
| Recorded participation | 2.0 | Fewer than 2 completed interviews in the past 30 days | 0 | 2 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 303

Pre-run judgment: Python/SQL/AWS evidence and four relevant projects fit cloud/data work. EE excludes the original Python Backend drive. Uneven communication/interview evidence suggests Ready rather than the highest band; no cloud skill gaps or low interview trigger.

Readiness: **78/100, Ready**. Your recorded profile totals 78/100 (Ready) under this weighted rule; projects is your strongest recorded factor and interview is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 78.99 | 30 | 23.7 | Mean of 5 self-reported skill proficiencies. |
| Projects | 100.0 | 20 | 20.0 | 4 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 79.9 | 15 | 11.99 | CGPA 7.99/10 x 10. |
| Aptitude | 71.76 | 15 | 10.76 | Self-reported existing assessment: 71.76/100. |
| Communication | 56.95 | 10 | 5.7 | Self-reported existing assessment: 56.95/100. |
| Interview | 56.84 | 10 | 5.68 | Self-reported existing assessment: 56.84/100. |

Support: **0/3 indicators**, flag **False** for Simulated Cloud Support Track. 0/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 0.0 | 3 or more role skill gaps | 0 | 0 gaps for Simulated Cloud Support Track: none. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 56.84 | Recorded interview score below 40/100 | 0 | Existing self-reported interview score is 56.84/100; the proposed support threshold is below 40. |
| Recorded participation | 3.0 | Fewer than 2 completed interviews in the past 30 days | 0 | 3 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 304

Pre-run judgment: High frontend proficiencies, four projects, strong academics and interview evidence suggest the highest band. The support rule is not triggered despite a different cloud role's skill gaps.

Readiness: **87/100, Highly Employable**. Your recorded profile totals 87/100 (Highly Employable) under this weighted rule; projects is your strongest recorded factor and aptitude is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 85.36 | 30 | 25.61 | Mean of 5 self-reported skill proficiencies. |
| Projects | 100.0 | 20 | 20.0 | 4 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 90.8 | 15 | 13.62 | CGPA 9.08/10 x 10. |
| Aptitude | 72.77 | 15 | 10.92 | Self-reported existing assessment: 72.77/100. |
| Communication | 74.03 | 10 | 7.4 | Self-reported existing assessment: 74.03/100. |
| Interview | 90.48 | 10 | 9.05 | Self-reported existing assessment: 90.48/100. |

Support: **1/3 indicators**, flag **False** for Simulated Cloud Support Track. 1/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 3.0 | 3 or more role skill gaps | 1 | 3 gaps for Simulated Cloud Support Track: python 0/60, sql 0/60, aws 0/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 90.48 | Recorded interview score below 40/100 | 0 | Existing self-reported interview score is 90.48/100; the proposed support threshold is below 40. |
| Recorded participation | 2.0 | Fewer than 2 completed interviews in the past 30 days | 0 | 2 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 306

Pre-run judgment: Three backlogs restrict most graduate drives; the cloud track and apprenticeships allow them. Missing interview evidence should reduce the weighted readiness view but must stay unknown for support, never be treated as poor performance.

Readiness: **60/100, Developing**. Your recorded profile totals 60/100 (Developing) under this weighted rule; academics is your strongest recorded factor and interview is a useful next area to review. Missing information contributes zero, which is not a judgment of your ability.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 61.03 | 30 | 18.31 | Mean of 5 self-reported skill proficiencies. |
| Projects | 75.0 | 20 | 15.0 | 3 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 76.1 | 15 | 11.42 | CGPA 7.61/10 x 10. |
| Aptitude | 63.82 | 15 | 9.57 | Self-reported existing assessment: 63.82/100. |
| Communication | 53.5 | 10 | 5.35 | Self-reported existing assessment: 53.5/100. |
| Interview | 0.0 | 10 | 0.0 | Assessment not recorded; contributes zero. |

Support: **1/3 indicators**, flag **False** for Simulated Cloud Support Track. 1/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure. The missing interview score needs clarification.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 1.0 | 3 or more role skill gaps | 0 | 1 gaps for Simulated Cloud Support Track: python 56.69/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | None | Recorded interview score below 40/100 | 0 | Interview score is missing; do not infer low performance. |
| Recorded participation | 1.0 | Fewer than 2 completed interviews in the past 30 days | 1 | 1 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 307

Pre-run judgment: A web specialism with just one project and a low interview score suggests development is still needed. ME excludes the original React drive. Two recorded completed interviews prevent the AND support flag despite cloud skill gaps and a low interview score.

Readiness: **54/100, Developing**. Your recorded profile totals 54/100 (Developing) under this weighted rule; academics is your strongest recorded factor and projects is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 61.12 | 30 | 18.34 | Mean of 5 self-reported skill proficiencies. |
| Projects | 25.0 | 20 | 5.0 | 1 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 79.8 | 15 | 11.97 | CGPA 7.98/10 x 10. |
| Aptitude | 69.22 | 15 | 10.38 | Self-reported existing assessment: 69.22/100. |
| Communication | 52.66 | 10 | 5.27 | Self-reported existing assessment: 52.66/100. |
| Interview | 32.32 | 10 | 3.23 | Self-reported existing assessment: 32.32/100. |

Support: **2/3 indicators**, flag **False** for Simulated Cloud Support Track. 2/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 4.0 | 3 or more role skill gaps | 1 | 4 gaps for Simulated Cloud Support Track: python 0/60, sql 0/60, aws 0/60, git 47.67/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 32.32 | Recorded interview score below 40/100 | 1 | Existing self-reported interview score is 32.32/100; the proposed support threshold is below 40. |
| Recorded participation | 2.0 | Fewer than 2 completed interviews in the past 30 days | 0 | 2 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 313

Pre-run judgment: Entry-level roles fit modest frontend/git/communication proficiencies and two projects better than graduate roles. For the cloud target, multiple skill gaps, low interview score and no completed interview activity justify a support review.

Readiness: **49/100, Developing**. Your recorded profile totals 49/100 (Developing) under this weighted rule; communication is your strongest recorded factor and interview is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 37.99 | 30 | 11.4 | Mean of 5 self-reported skill proficiencies. |
| Projects | 50.0 | 20 | 10.0 | 2 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 60.0 | 15 | 9.0 | CGPA 6/10 x 10. |
| Aptitude | 59.34 | 15 | 8.9 | Self-reported existing assessment: 59.34/100. |
| Communication | 66.84 | 10 | 6.68 | Self-reported existing assessment: 66.84/100. |
| Interview | 30.85 | 10 | 3.09 | Self-reported existing assessment: 30.85/100. |

Support: **3/3 indicators**, flag **True** for Simulated Cloud Support Track. 3/3 support indicators meet the proposed thresholds. This student may benefit from technical, interview-preparation and mentoring support; an administrator should review the evidence and context.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 4.0 | 3 or more role skill gaps | 1 | 4 gaps for Simulated Cloud Support Track: python 0/60, sql 0/60, aws 0/60, git 38.93/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 30.85 | Recorded interview score below 40/100 | 1 | Existing self-reported interview score is 30.85/100; the proposed support threshold is below 40. |
| Recorded participation | 0.0 | Fewer than 2 completed interviews in the past 30 days | 1 | 0 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |
- Technical: Offer focused practical training in python, sql, aws, git; review evidence after practice.
- Interview preparation: Arrange a mentor-led practice session and review the existing assessment; no automated mock-interview feature is used.
- Mentoring: Check whether suitable drives were available and attendance was recorded; agree on one achievable next participation step.

### Seed 315

Pre-run judgment: Three backlogs narrow options, while Python projects and lower-threshold support roles remain plausible. Weak aptitude/communication and incomplete skill targets suggest Developing. Interview score is above the support cutoff and activity is adequate.

Readiness: **44/100, Developing**. Your recorded profile totals 44/100 (Developing) under this weighted rule; academics is your strongest recorded factor and communication is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 48.07 | 30 | 14.42 | Mean of 5 self-reported skill proficiencies. |
| Projects | 50.0 | 20 | 10.0 | 2 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 57.8 | 15 | 8.67 | CGPA 5.78/10 x 10. |
| Aptitude | 30.23 | 15 | 4.53 | Self-reported existing assessment: 30.23/100. |
| Communication | 17.56 | 10 | 1.76 | Self-reported existing assessment: 17.56/100. |
| Interview | 44.63 | 10 | 4.46 | Self-reported existing assessment: 44.63/100. |

Support: **1/3 indicators**, flag **False** for Simulated Cloud Support Track. 1/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 4.0 | 3 or more role skill gaps | 1 | 4 gaps for Simulated Cloud Support Track: python 59.3/60, sql 38.54/60, aws 49.89/60, git 41.56/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 44.63 | Recorded interview score below 40/100 | 0 | Existing self-reported interview score is 44.63/100; the proposed support threshold is below 40. |
| Recorded participation | 2.0 | Fewer than 2 completed interviews in the past 30 days | 0 | 2 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 318

Pre-run judgment: Python/SQL/AWS are stronger than the single recorded project and low interview result. Graduate roles allowing one backlog remain plausible. Only git is below the cloud target, so the combined support flag should not trigger.

Readiness: **51/100, Developing**. Your recorded profile totals 51/100 (Developing) under this weighted rule; academics is your strongest recorded factor and projects is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 58.02 | 30 | 17.41 | Mean of 5 self-reported skill proficiencies. |
| Projects | 25.0 | 20 | 5.0 | 1 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 77.3 | 15 | 11.6 | CGPA 7.73/10 x 10. |
| Aptitude | 55.76 | 15 | 8.36 | Self-reported existing assessment: 55.76/100. |
| Communication | 46.75 | 10 | 4.68 | Self-reported existing assessment: 46.75/100. |
| Interview | 34.46 | 10 | 3.45 | Self-reported existing assessment: 34.46/100. |

Support: **1/3 indicators**, flag **False** for Simulated Cloud Support Track. 1/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 1.0 | 3 or more role skill gaps | 0 | 1 gaps for Simulated Cloud Support Track: git 47.32/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 34.46 | Recorded interview score below 40/100 | 1 | Existing self-reported interview score is 34.46/100; the proposed support threshold is below 40. |
| Recorded participation | 2.0 | Fewer than 2 completed interviews in the past 30 days | 0 | 2 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

### Seed 320

Pre-run judgment: SQL/git projects, moderate Java and stronger communication/interview evidence suggest entry-level Java/QA/support fits. Three projects do not erase the uneven skills and aptitude. Interview score is not low, so no combined support flag.

Readiness: **61/100, Developing**. Your recorded profile totals 61/100 (Developing) under this weighted rule; projects is your strongest recorded factor and aptitude is a useful next area to review.

| Factor | Normalized input | Weight | Contribution | Evidence |
|---|---|---|---|---|
| Technical skills | 53.96 | 30 | 16.19 | Mean of 4 self-reported skill proficiencies. |
| Projects | 75.0 | 20 | 15.0 | 3 recorded projects x 25 points, capped at 100; quality is not assessed. |
| Academics | 64.8 | 15 | 9.72 | CGPA 6.48/10 x 10. |
| Aptitude | 38.96 | 15 | 5.84 | Self-reported existing assessment: 38.96/100. |
| Communication | 70.66 | 10 | 7.07 | Self-reported existing assessment: 70.66/100. |
| Interview | 69.14 | 10 | 6.91 | Self-reported existing assessment: 69.14/100. |

Support: **2/3 indicators**, flag **False** for Simulated Cloud Support Track. 2/3 support indicators meet the proposed thresholds. The combined support rule is not triggered; this is not a prediction of success or failure.

| Factor | Observed input | Threshold | Contribution | Evidence |
|---|---|---|---|---|
| Technical support | 3.0 | 3 or more role skill gaps | 1 | 3 gaps for Simulated Cloud Support Track: python 0/60, aws 0/60, git 59.81/60. Targets and proficiencies are proposed/self-reported. |
| Interview preparation | 69.14 | Recorded interview score below 40/100 | 0 | Existing self-reported interview score is 69.14/100; the proposed support threshold is below 40. |
| Recorded participation | 1.0 | Fewer than 2 completed interviews in the past 30 days | 1 | 1 completed interview record(s) in the last 30 days. This is not a measure of effort; verify opportunities and missing records. |

## Dataset check

Observed synthetic population: **4800 students and 45 companies**. Outcomes are fictional imports from proposed correlated generation assumptions, not observed placements. Earlier 300 profiles and four support examples are preserved; new profiles share a noisy preparation factor. Selected, active accepted and joined are distinct counts.

| CGPA group | Students | Selected | Active accepted offers (students) | Joined |
|---|---|---|---|---|
| CGPA 6 to below 8 | 2481 | 1213 | 717 | 368 |
| CGPA 8 or above | 1397 | 943 | 561 | 267 |
| CGPA below 6 | 922 | 227 | 139 | 65 |

Counts come from the actual seeded records. Compare each outcome count with its group's student count; this describes a deliberately generated association, not a real placement forecast.

## Limits

- No real data or independent human rater.
- Convenience sample of ten profiles; no expected Not Ready example.
- Expected roles reflect specialization and appropriate level; the weighted engine measures requirement coverage and may favor easier roles.
- Correlations and outcomes are deliberately generated, not learned or validated.
- No weights, thresholds, labels or inputs were tuned to the observed result.

Full matching scores, factors, missing requirements and fixed explanations for every evaluated profile/role are retained in phase4-results.json. No bare score is used as an evaluation conclusion.
