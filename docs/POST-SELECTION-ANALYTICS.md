# Post-selection journey and recorded closures

This administrator view describes saved selection and offer milestones. It does not predict dropout, independently verify employment, or change a student's score, interview, or offer. The implementation uses existing tables and adds no dependency.

## Open the view

1. Sign in through **Admin** for your college using an existing allowlisted, email-verified administrator account.
2. Open **Overview**, then scroll below **04 Recorded offer outcomes** to **05 Post-selection journey**.
3. **Journey records** defaults to **Recorded college workflow**. This excludes explicitly synthetic offers, seed-marked interview pairs, and every record in archived demo colleges 1 and 2. An empty real college therefore shows an empty view rather than fictional placements.
4. To rehearse in an archived demo college, choose **Synthetic and archived demo workflow**. **All recorded workflow** includes both kinds and displays their counts explicitly.
5. Choose a **Journey drive** or leave **All college drives** selected. Drive choices are limited to your college, even when a scope has no outcomes.
6. Click **Refresh journey and reasons** after a recorded workflow change. The normal dashboard refresh also refreshes this view; its separate timestamp remains visible.
7. Review the chart together with its table, then **Independent milestone evidence**, **Recorded terminal closures**, the exact reasons and their source, and **Evidence coverage and missing history**. Use reason pagination if needed.

The view is read-only. Record selection, issue a letter, accept, verify, or record joining through the existing role-owned workflow controls. Verification and acceptance remain independent human actions. Do not manufacture an outcome to make the chart complete.

## Counting unit and denominator

The cohort is a **distinct student–drive pair** with a currently selected interview, valid historical selection evidence, or a consistently linked offer. Offer creation already requires selection. Multiple interview rounds for the same student and drive count once. The database permits at most one offer for that pair. A student selected in two different drives counts as two pairs, while each displayed distinct-student count deduplicates that stage separately.

| Cumulative stage | Evidence required for the same pair |
|---|---|
| Selected | Selection evidence |
| Letter issued | Selection and ever-recorded issuance |
| Accepted | All preceding milestones and ever-recorded acceptance |
| Accepted and verified | All preceding milestones and ever-recorded verification |
| Joined | All preceding milestones and ever-recorded joining |

This is a presentation order, not a claim about event timing. Verification can be recorded without acceptance; the independent milestone list exposes that separately. Current statuses and valid before/after audit snapshots preserve reached milestones after a withdrawal or later human correction. These historical counts differ intentionally from the existing totals of currently active accepted offers.

Each conversion displays the reached-pair count divided by the preceding cumulative stage. A zero denominator returns an unavailable rate, never a fabricated zero-percent outcome. Each stage also partitions pairs that have not reached it into those with and without a recorded terminal offer closure. Neither category predicts a student's future; absence of a closure does not establish that a process is still active.

## Closures, reasons, and evidence quality

Only explicit current offer withdrawal, student decline, or recorded non-joining counts as a terminal closure. For contradictory legacy statuses, one pair is counted once using **withdrawn → declined → not_joined** precedence. One student may nevertheless appear in multiple categories through different drives; distinct-student counts must not be added across categories or stages.

Reasons are grouped by closure, evidence source, and exact retained text:

- **Recorded action reason:** a matching offer action's literal audit reason.
- **Synthetic import note:** an explicitly labeled data-generation note, not an observed employer or student explanation.
- **No audited reason recorded:** no usable matching reason is available; no cause is invented.

The evidence panel reports missing offer history, invalid/mismatched snapshots, inconsistent linked interviews, issuance gaps, and selection evidenced only by history or an offer. Malformed or contradictory event identities are excluded from historical milestone evidence and reported. Current declared statuses remain visible without inventing missing historical transitions. The view does not infer dates, elapsed time, a retention rate, or causality from incomplete history.

## API and tenant boundaries

`GET /admin/analytics/post-selection` accepts `scope=recorded|synthetic|all`, optional positive `job_id`, nonnegative `offset`, and `limit` from 1 to 50 (default 20). Pagination applies to grouped reasons, with `reason_total` for navigation. An unknown or cross-college drive returns 404; student/recruiter access is denied by the existing administrator dependency. Every projected table query retains an explicit `college_id` filter. Existing PostgreSQL ENABLE/FORCE `college_isolation` policies remain the independent second layer; this feature introduces no tenant table and leaves the inventory at 30.

## Verification status

Published implementation commit `955e28c` serves API **0.15.0**. All **158 backend regression cases**, **13 new frontend checks** (including actual PostgreSQL response samples), **19 navigation checks**, **19 dashboard checks**, and the production build pass. A local PostgreSQL-backed dummy administrator/browser rehearsal verifies record and drive filters, stage denominators, and human versus synthetic reason sources. Render reports this source commit Live and Vercel reports a successful deployment.

All **37 live public/owned-synthetic release checks** pass, including the served dashboard controls, exact CORS origin, student/recruiter denial of administrator analytics, and the actual thirty-table FORCE-RLS catalog. Two earlier runs stopped on transport timeouts with no failing returned assertions; the complete run uses the already installed HTTP client's connection pool, with no production-code change. Results and diagnostics are retained in `evaluations/post-selection-analytics.json`.

**Still pending:** the authenticated live administrator read and owner acceptance. The prepared live Admin tab currently shows sign-in. A served control and role-denial checks do not prove an authorized live administrator body rendered. After the owner signs in, follow the steps above; an archived demo college correctly has an empty default recorded view and requires the explicitly synthetic/archive filter for rehearsal. No live hiring/file mutation or external message was made by these analytics release checks.

Other backlog work remains separate: staff-verified assessment provenance, fairness evaluation, actual real-account inbox/approval verification, password recovery/rate limits/session revocation, responsible-data controls, and verified backup/restore/monitoring/database continuity. The Render dashboard was checked on October 4, 2026: the current free database is available and states an expiry of **October 21, 2026**. This analytics release does not resolve that deadline.
