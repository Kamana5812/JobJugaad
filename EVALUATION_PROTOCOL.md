# Phase 4 synthetic evaluation protocol

This is an **assistant-authored synthetic sanity check against our own assumptions**, not independent human validation, calibrated confidence or real-world accuracy. No trained model is evaluated. The expected labels below are manually reasoned from raw generated inputs and declared drive requirements before invoking evaluation engines.

## Frozen sample and expectations

The ten seed indices are 301, 302, 303, 304, 306, 307, 313, 315, 318 and 320. This is an intentionally selected, small convenience sample spanning Python, frontend and Java specialisms, weaker assessments, backlogs and missing interview evidence. It is not a random holdout, does not represent prevalence and does not cover an expected Not Ready case. Both scoring reviews use exactly the same ten profiles. An independent human reviewer has not supplied these labels.

Expected role choices, readiness bands, cloud-role support flags, qualitative rationales and raw-input hashes are frozen in backend/evaluation_expected.json. Their ordering expresses the reviewer's judgment of suitable role/level; hit counting uses set overlap with the engine's three highest-scored eligible jobs. Only the thirteen declared simulated drives (three original drives, the cloud support track and nine Phase 4 roles) enter this comparison. Ties use the documented fixed catalog order, not mutable database IDs. Actual top-three results may contain fewer than three eligible jobs; excluded candidates are never promoted for the evaluation.

## Execution and reporting

1. Seed the reproducible inputs without changing existing records. Confirm the actual database inputs match the frozen hashes; report drift as an error rather than silently updating expectations.
2. Run the unchanged weighted Matching Engine against each sample profile and the fixed role catalog, apply each drive's eligibility rules and threshold, and sort eligible jobs by descending score.
3. Report how many of the **30 expected matches** appear in the actual lists, along with the actual list sizes, missed and unexpected roles and explanatory factors. Micro precision is hits / actual returned slots and recall is hits / 30; report as counts/fractions, not validated accuracy percentages.
4. Run the weighted Readiness Engine and the simple support thresholds against the same inputs. Compare each readiness band and flag with its frozen expectation. Support uses Simulated Cloud Support Track and the sample's recorded completed interview count at evaluation time.
5. Preserve every mismatch. Do not alter weights, thresholds, profiles or labels to improve the reported count. Inspect mismatches and explain observable reasons or limitations.
6. Save the observed report plus full machine-readable factor breakdowns and explanations. The report is evidence of consistency with these assumptions only. Dataset correlations were deliberately generated; they do not validate a real hiring model.

The sample and all employer requirements are fictional. The support flag is a suggestion for human review, not a prediction of failure. Missing assessments remain explicitly unknown. Notifications and seeded outcomes are simulations. Any future trained support classifier must first handle class imbalance through SMOTE or class weighting and use a real evaluation protocol.
