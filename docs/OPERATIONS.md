# Operations and continuity

## Automated checks

GitHub Regression and restore drill runs on feature/main pushes and pull requests. It creates a disposable PostgreSQL 17 database with a non-superuser, non-BYPASSRLS application role, runs backend regression, verifies an encrypted scoped restore, checks navigation and builds the frontend. A successful local run is not evidence that the remote workflow passed. Deployment remains provider-managed; the workflow does not itself configure branch protection or guarantee a deployment waits for CI.

Live service health checks run approximately every thirty minutes and on manual workflow dispatch. They check database connectivity, actual enabled/forced/scoped policies, restricted runtime role, model readiness and frontend HTTP response. These are checks, not an uptime or performance benchmark. GitHub schedules may be delayed. Owners must enable failed-workflow notifications in GitHub; actual alert receipt requires verification.

## Encrypted tenant backup and restore

Use a private operator environment with PYTHONPATH=backend, DATABASE_URL set securely and BACKUP_ENCRYPTION_KEY set to a private Fernet key. Never commit keys, connection strings or archives. Supply every authorized tenant explicitly; an incomplete college list creates an incomplete backup. The tool includes private PDF bytes and authentication records inside the encrypted archive, with no plaintext file written.

```text
python -m operations.backup backup --path PRIVATE_NEW_ARCHIVE_PATH --colleges AUTHORIZED_COLLEGE_IDS
```

Store the encrypted archive and key separately in owner-controlled private storage. The command refuses to overwrite an archive. Keep a tenant inventory and backup date, coverage and digests. The service process filesystem is not durable off-site storage.

Restores are allowed only into an empty loopback database whose name starts jobjugaad_restore_, with ALLOW_RESTORE_DATABASE=yes. Provision the restricted application role and a new database; never point a rehearsal at the live database.

```text
python -m operations.backup restore-drill --path PRIVATE_ARCHIVE_PATH
```

Restore verifies the table inventory, college ownership, all restored rows and file bytes, and actual RLS. Restricted users and session versions are preserved. Reconcile deletion/retention decisions made since the backup before any restored service becomes available.

Local evidence: evaluations/backup-restore-local.json records 84 fixture rows across all 34 tables, with exact normalized row/byte equality and verified policies. This is not a production backup, off-site storage check or disaster recovery SLA.

## Retention and continuity

The retention utility defaults to a dry run:

```text
python -m operations.retention --college AUTHORIZED_COLLEGE_ID
```

Applying cleanup requires both --apply and --confirm-expired-security-records plus owner authorization for the deletion. It covers only expired security counters/challenges, not placement history or account erasure.

The recorded Render free database expiry is October 21, 2026, previously confirmed in the dashboard. Before that date, verify the current deadline, take a complete encrypted backup, verify a restore, provision an owner-approved durable destination, transfer server secrets privately, and check all policies and application workflows before switching DATABASE_URL. No paid upgrade is authorized, no production migration has occurred, and no free provider's availability is promised. A continuity plan is written; its production execution remains pending.
