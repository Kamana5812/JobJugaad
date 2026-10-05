# Database continuity execution checklist

## Observed state — October 5, 2026

The owner selected Neon's free PostgreSQL plan. The signed-in create-project
form is prepared for `jobjugaad` in AWS Singapore, PostgreSQL only. It displays
0.5 GB storage, scale to zero, autoscaling up to 2 CU and ten branches. Project
creation and migration are not yet confirmed. Use the actual account quota,
not a different public offer. Existing unrelated Neon projects are untouched.

Render's previously verified database expiry is October 21, 2026. The existing
database remains the source of truth until a verified cutover. No paid upgrade,
production deletion, production archive or destination import has occurred.

## Execute in order

1. Owner creates the prepared free project. Keep credentials private. Provision
   a dedicated application role with NOSUPERUSER and NOBYPASSRLS; do not use an
   administrative/default provider role for the API. Preserve SSL verification.
2. In a private operator environment, measure `pg_database_size(current_database())`,
   table/index/file storage and expected headroom. Confirm the destination quota
   before uploading anything. This catalog SQL is read-only maintenance.
3. Inventory every active and archived college. The existing scoped backup
   requires an explicit complete college list; a backup of college 219 alone
   does not protect the other tenants. Inspect source schema/roles/sequences,
   row counts and all 34 RLS policies, without printing credentials or records.
4. Arrange a maintenance window that pauses writes. Produce a complete encrypted
   tenant archive with `operations.backup`, including private PDF bytes. Store
   the archive and encryption key separately in private owner-controlled storage.
   Record time, coverage, hashes and counts; never commit an archive or key.
5. Restore the archive into a new empty local drill database and verify every
   normalized row/file byte, sequence and policy. The existing restore tool is
   deliberately local-only; do not weaken its guard for a remote import.
6. Prepare a separately reviewed destination migration preserving identities,
   constraints, sequences, ENABLE/FORCE policies and restricted role. Import only
   into an empty approved destination. Reconcile pending deletion/retention
   decisions and check all tenant counts against the frozen source snapshot.
7. Test student/recruiter/admin access, authentication and session versions,
   announcements, document downloads, scheduling, assessments and analytics on
   the destination before updating Render's DATABASE_URL privately.
8. Cut over during the same write pause. Recheck live health, all 34 policies,
   direct cross-college denial and role workflows. Keep the old source intact
   until acceptance. Roll back only before new destination writes, or reconcile
   those writes explicitly; blindly switching back can lose new records.
9. Confirm backups can be retrieved and restored from owner storage, establish
   retention/rotation and alert receipt, then record completion in MEMORY.md.

## Read-only erasure inventory

`python -m operations.erasure_inventory --college COLLEGE_ID --user USER_ID`

This reports counts across all 34 modeled tables without outputting account
content, secrets or file bytes. It follows downstream foreign keys, including
indirect document/event dependencies and shared audit actor references. Shared
records are not automatically safe to delete. JSON snapshots, free text,
limiter hashes and off-site copies need separate review. There is no apply mode.

Permanent erasure requires a college-approved policy identifying retention
grounds, expiry, legal holds, audit anonymization and backup reconciliation.
The existing 30-day value is a review deadline, not automatic erasure. Until
those decisions and a reviewed execution path exist, permanent erasure remains
incomplete; account restriction must not be presented as deletion.

## Live monitoring evidence

The existing public health workflow was manually dispatched on October 5 and
completed successfully: https://github.com/Kamana5812/JobJugaad/actions/runs/37259593089.
This verifies remote execution, not failure-alert receipt. The owner still needs
to confirm GitHub failed-workflow notification delivery; no outage was induced.
