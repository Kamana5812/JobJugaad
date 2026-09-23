"""Read-only PostgreSQL catalog verification; no tenant records or secrets returned."""
import re
from sqlalchemy import text

PREDICATE = "college_id = NULLIF(current_setting('app.college_id', true), '')::integer"


def _normalized(expression):
    # PostgreSQL deparses redundant parentheses and explicit text casts.
    return re.sub(r"[\s()]", "", (expression or "").replace("::text", ""))


def audit_isolation(connection):
    """Catalog SQL is necessary: ORM metadata cannot prove deployed RLS policies."""
    from database import Base
    import models  # register every core table
    safe_role = not connection.execute(text(
        "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
    )).scalar_one()
    catalog = connection.execute(text("""
        SELECT c.relname AS name, c.relrowsecurity AS enabled, c.relforcerowsecurity AS forced
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = current_schema() AND c.relkind IN ('r', 'p')
        AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid
                    AND a.attname = 'college_id' AND NOT a.attisdropped)
    """)).mappings().all()
    tables = {row['name']: row for row in catalog}
    policies = connection.execute(text("""
        SELECT tablename, policyname, permissive, roles, cmd, qual, with_check
        FROM pg_policies WHERE schemaname = current_schema()
    """)).mappings().all()
    expected = {table.name for table in Base.metadata.sorted_tables}
    rows = []
    for name in sorted(expected | tables.keys()):
        table = tables.get(name)
        entries = [p for p in policies if p['tablename'] == name]
        policy = entries[0] if len(entries) == 1 else None
        predicate_ok = bool(policy and policy['policyname'] == 'college_isolation'
            and policy['cmd'] == 'ALL' and policy['permissive'] == 'PERMISSIVE'
            and list(policy['roles']) == ['public']
            and _normalized(policy['qual']) == _normalized(PREDICATE)
            and _normalized(policy['with_check']) == _normalized(PREDICATE))
        enabled, forced = bool(table and table['enabled']), bool(table and table['forced'])
        rows.append(dict(table=name, college_id=table is not None, enabled=enabled,
            forced=forced, policy='college_isolation' if predicate_ok else None,
            read_write_scoped=predicate_ok,
            status='verified' if enabled and forced and predicate_ok and name in expected else 'failed'))
    return dict(status='verified' if safe_role and all(r['status'] == 'verified' for r in rows) else 'failed',
        runtime_role_restricted=safe_role, tables=rows)


def require_isolation(connection):
    report = audit_isolation(connection)
    if report['status'] != 'verified':
        raise RuntimeError('Database isolation verification failed.')
    return report
