# Synthetic matching fairness review

This is a synthetic rule-behavior audit against our own assumptions, not independently validated fairness or accuracy.

Evaluated 4796 seeded profiles across three simulated drives. Twelve controlled pairs change only CGPA from 5.5 to 9.0; 8 pairs change eligibility.

| Drive | CGPA group | Eligible / profiles | CGPA-floor exclusions | Strong-evidence exclusions / profiles |
|---|---|---|---|---|
| Simulated Python Backend Engineer | 6.5 to below 8 | 370 / 1915 | 0 | 222 / 541 |
| Simulated Python Backend Engineer | 8 and above | 527 / 1397 | 0 | 146 / 468 |
| Simulated Python Backend Engineer | below 6.5 | 75 / 1484 | 922 | 144 / 199 |
| Simulated React Frontend Engineer | 6.5 to below 8 | 450 / 1915 | 0 | 200 / 577 |
| Simulated React Frontend Engineer | 8 and above | 850 / 1397 | 0 | 68 / 417 |
| Simulated React Frontend Engineer | below 6.5 | 0 / 1484 | 1484 | 179 / 179 |
| Simulated Java Graduate Engineer | 6.5 to below 8 | 564 / 1915 | 0 | 59 / 585 |
| Simulated Java Graduate Engineer | 8 and above | 441 / 1397 | 0 | 0 / 435 |
| Simulated Java Graduate Engineer | below 6.5 | 202 / 1484 | 524 | 71 / 224 |

Strong evidence means skill compatibility at least 80/100 and project relevance at least 50/100. Exclusions can combine branch, backlogs, CGPA and weighted threshold; the table does not attribute every exclusion to CGPA. Full branch comparisons, paired factor breakdowns and fixed explanations are in fairness-results.json.

CGPA floors can exclude skilled profiles before ranking; academic weighting also changes the score with identical other inputs. The correlated synthetic dataset naturally favors stronger academic profiles in several inputs, so aggregate differences do not isolate causation. Review floors with recruiters, inspect complete evidence, and log human exceptions rather than silently changing weights. No protected-group parity claim is possible because representative protected-group data is not collected. Samples below thirty are explicitly flagged. This report establishes observable rule behavior, not real-world fairness.

No matching rules, weights or thresholds were changed by this evaluation.
