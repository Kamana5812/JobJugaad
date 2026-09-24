# Public placement model integration — 2026-09-24

User authorized integration after seeing the measured holdout results and clarified that the public dataset need not originate from BPUT. This extends the existing deployment; it does not replace the synthetic workflow dataset.

## What is real and what remains simulated

The imported Campus Recruitment CSV contains 215 public labeled placement records, with source/license/checksum in backend/data/. The saved Random Forest was fitted on 172 and tested on 43. Measured accuracy is 38/43 (88.37%), Placed precision 93.10%, recall 90.00%, F1 91.53%; confusion matrix actual rows/predicted columns [Not Placed, Placed] is [[11,2],[3,27]]. The frozen training report is historical evidence, not a current deployment-status document.

The 4,800-profile tenant demonstration, skills, projects, certificates, matching, schedules and offers remain explicitly synthetic. Public records are not imported as fictional named accounts, nor given invented skills or offers. User-entered academic inputs are separate from the source dataset. The weighted readiness and support formulas remain unchanged.

## Model contract and deployment

GET/PUT /students/{student_id}/placement-model accepts only 12 optional validated predictors. Missing evidence yields no score and a named reason; percentages must be finite and in 0–100, categories must match the trained schema. A student may clear saved fields to withdraw the signal. Student ownership and explicit college_id filters protect every read/write. The new placement_model_profiles table is created atomically with ENABLE/FORCE college_isolation RLS and a composite student/college foreign key, bringing the total to 18 tenant tables.

The checksum-verified trusted local joblib pipeline loads once per process, using pinned dependency versions; it never retrains at startup or per request. A load failure leaves the ordinary workflow available and returns an unavailable model, visible in /health. Do not load user-uploaded models. Single-process loading and n_jobs=1 avoid duplicated model workers; no production capacity claim is made.

Each available signal supplies an uncalibrated score out of 100, training-root baseline, all 12 signed original-field contributions and a fixed explanation. Tree-path probability changes telescope to each leaf; averaging reconstructs the forest output. Encoding contributions are grouped back to their source field. This is descriptive model attribution, not causal evidence, a calibrated chance, or SHAP. It is not used by recruiters for eligibility, matching, rejection, offers or support flags. Gender/education bias and transfer to other cohorts have not been evaluated.

## Verification

Four integration tests passed against local PostgreSQL: owned profile roundtrip/validation and unchanged weighted readiness, cross-college read/write and same-college ownership denial, missing evidence/artifact checksum failure, and additive explanations agreeing with the saved forest on all 215 public rows. The first run lacked a running local database; the first connected run exposed shared test setup, which was corrected before the successful run.

Verification: 46 test cases passed across the full regression and targeted retests. The full run was interrupted for over six hours and finished 45/46; the final matching case lacked its expected authenticated response. All eight matching tests passed in a fresh run. Four model integration tests passed again after tightening the explicit college filter on updates. The production Vite build, actual-output rendering for available/missing/unsaved states, dependency check and whitespace check passed. Browser automation cannot initialize on this machine, so no interactive browser or Swagger UI test is claimed. Live deployment verification is pending.

## Student demonstration

1. Sign in to a student account and open My profile.
2. Read Weighted Readiness Score and its existing six-factor explanation.
3. Scroll to Placement Likelihood Model and open Add or edit academic model inputs.
4. Enter the student's actual compatible academic records. For a demonstration only, use a separate synthetic test account and clearly identify any copied public row as a public-record example, not that account holder's real history.
5. Save academic inputs & view model. Inspect the score, explanation, baseline and all 12 contributions.
6. Open Measured evaluation on public data to see sample sizes, measured metrics, confusion matrix and the source link.
7. Clear an input and save: the model score becomes unavailable; weighted readiness remains unchanged.
