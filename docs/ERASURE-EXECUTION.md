# Governed erasure execution

The account request/restriction workflow is separate from permanent erasure. The thirty-day value is a review deadline; the college must decide lawful retention grounds, holds, period and approval authority. No live deletion is authorised by a generic feature-implementation request.

`python -m operations.erasure --college COLLEGE_ID --user USER_ID` creates a read-only scoped plan. It follows owned student rows, events and file bytes; references in records belonging to others are blockers. Recruiter and administrator accounts are refused because shared placement ownership and succession require a separate decision. The plan contains IDs/counts, not passwords or file content.

For an explicitly approved student erasure, a private JSON manifest must contain the current `plan_hash`, `approved_by`, `reason`, `backup_disposition` and `residual_identity_review`. Only a disabled account with an expired `restricted_pending_erasure` request is eligible. Review the complete dependency inventory and retained JSON/free-text mentions separately. Use a private new receipt filename and an owner-approved manifest with `--apply --approved-manifest PATH --receipt PATH`. Never commit either file. Obtain explicit owner approval before running this destructive operation on production.

Execution locks the account/college, rejects stale plans/shared references, breaks only nullable owned cycles, deletes leaf dependencies within one transaction, and retains foreign keys and RLS throughout. Any unresolved constraint causes rollback. The receipt records exactly what was erased. It does not claim that provider backups, old encrypted archives, hashed security-counter records or references outside owned rows vanished.

Backups require a separately approved disposal/retention process. Keep an owner-controlled erasure ledger with the receipt; before any restore/import, reconcile that ledger so erased accounts are not resurrected. Deleting a whole shared-college archive may destroy others' continuity and requires explicit approval. Do not erase encryption keys or backup files casually. Until external copies and residual references are verified, report database erasure separately from all-copy erasure.

Local regression uses disposable fixture accounts only and checks atomic erasure, retention rejection, stale-manifest rejection and cross-college denial. No production records are changed by those tests.
