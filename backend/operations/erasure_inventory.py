"""Read-only account dependency inventory; never delete or claim complete erasure."""
import argparse
import json
from sqlalchemy import or_, select
from database import Base, tenant_session
import models


def inventory(college_id, user_id):
    """Follow downstream tenant-scoped foreign keys, including indirect file history.

    Shared actor references are included conservatively. JSON/free-text evidence,
    authentication limiter hashes and off-site backups require separate review.
    Nothing in this inventory is automatic authorization to delete a row.
    """
    if college_id < 1 or user_id < 1:
        raise ValueError('Positive college and account identifiers required.')
    tables = Base.metadata.tables
    affected = {name: set() for name in tables}
    with tenant_session(college_id) as session:
        user = session.execute(select(models.User.id).where(
            models.User.college_id == college_id, models.User.id == user_id)).scalar_one_or_none()
        if user is None:
            raise ValueError('Account not found in the selected college.')
        affected['users'].add(user)
        changed = True
        while changed:
            changed = False
            for name, table in tables.items():
                conditions = []
                for fk in table.foreign_keys:
                    target = fk.column
                    if target.name == 'id' and affected[target.table.name]:
                        conditions.append(fk.parent.in_(sorted(affected[target.table.name])))
                if not conditions:
                    continue
                found = set(session.scalars(select(table.c.id).where(
                    table.c.college_id == college_id, or_(*conditions))))
                if found - affected[name]:
                    affected[name].update(found)
                    changed = True
    return {
        'college_id': college_id, 'user_id': user_id, 'read_only': True,
        'table_counts': {name: len(ids) for name, ids in sorted(affected.items())},
        'permanent_erasure_completed': False,
        'limitations': [
            'Counts include shared records referring to this account as an audit actor; do not cascade-delete them.',
            'JSON snapshots, free text and hashed security counters need separate identity review.',
            'Off-site archives, replicas and provider retention are outside this database inventory.',
            'College-approved retention grounds, legal holds and administrator succession must be reviewed before erasure.',
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--college', type=int, required=True)
    parser.add_argument('--user', type=int, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(inventory(args.college, args.user), indent=2))
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__}))
        raise SystemExit(1)
