# External assessment evidence

College administrators can record reviewed external aptitude, communication,
interview or named-skill results. Students can read only their own records.
Recruiters cannot browse these records in this release. Staff entry is a human
declaration, not independent exam authentication, proctoring or an automated
verification service. No exam, mock interview or new trained model is built.

## Record a result

1. Sign in as your college administrator and open **Assessment evidence**.
2. Enter the student's existing ID in your college, assessment type, title,
   provider/source, result reference and the assessment's actual date/time.
3. Enter the original score and maximum, then describe what source you reviewed.
4. Choose **Record reviewed result**. The record shows its creator and timestamp,
   original scale, and `score / maximum × 100` normalization with an explanation.
5. The student opens **Assessment evidence** below readiness and refreshes to
   see the same original result, provenance and review context.
6. For an incorrect record, expand **Withdraw an incorrect record**, give a reason,
   and choose **Withdraw record · keep history**. Add a new reviewed result for
   a correction. Original scores and the single withdrawal remain visible.

Unknown results must not be invented. Existing synthetic/self-reported profile
fields are never relabeled as staff-reviewed evidence. No real assessment records
are seeded. Manual entry is supported; CSV import is not implemented.

## Scoring boundary

Readiness retains its 30/20/15/15/10/10 weighted rule. Evidence-only is the default.
An administrator can explicitly adopt a reviewed result using the checkbox before
recording it. Active adopted results replace the corresponding aptitude,
communication, interview or exact skill input; latest assessment date wins, ties
by record ID. Each scoring factor names the result, source, reference, scale,
date and recorder. Original self-reports are not overwritten. Withdrawal restores
the previous active adopted result, or the self-report if none remains. Readiness
and its cached overview value refresh; matching/support snapshots need a rerun.
Frozen applications and override evidence are not rewritten. The separately
trained public-data models do not adopt these assessment results.

## Access and history

The `assessments` table has application-level `college_id` filters, composite
student/reviewer tenant foreign keys, and an atomic ENABLE/FORCE PostgreSQL
`college_isolation` policy. Startup and `/health` verify it with the existing
catalog audit. Administrator writes reuse the server allowlist and verified-account
checks. Student reads require ownership. There is no edit/delete API. Withdrawal
locks the row and rejects repeated changes, preserving reviewer, time and reason.
Database-owner tamper resistance, authenticity checking, evidence-file upload,
retention deletion, recruiter visibility and exam-platform integration are not
claimed. Lists are paginated, with an optional administrator student-ID filter.
