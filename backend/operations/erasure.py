"""Governed student-account erasure. Default is a read-only, tenant-scoped plan.

No cascade across shared actor references. Live use requires an owner-approved
retention decision, expired restricted request and a reviewed backup disposition.
An erased database account does not mean provider backups were erased.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import delete, or_, select, text, update
from database import Base, tenant_session
from models import User, Student, DataRequest

OWNERSHIP = {'user_id', 'recipient_user_id'}

def _plan(session, college, identity):
    tables = Base.metadata.tables
    owner = session.scalar(select(User).where(User.college_id == college, User.id == identity).with_for_update())
    if owner is None:
        raise ValueError('Account not found in this college.')
    if owner.role != 'student':
        raise ValueError('Shared recruiter and administrator records require a separate succession/retention review.')
    affected = {name: set() for name in tables}
    affected['users'].add(identity)
    changed = True
    while changed:
        changed = False
        for name, table in tables.items():
            conditions = []
            for fk in table.foreign_keys:
                target = fk.column
                if target.name != 'id' or not affected[target.table.name]:
                    continue
                if target.table.name == 'users' and fk.parent.name not in OWNERSHIP:
                    continue
                conditions.append(fk.parent.in_(sorted(affected[target.table.name])))
            if conditions:
                found = set(session.scalars(select(table.c.id).where(table.c.college_id == college, or_(*conditions))))
                if found - affected[name]:
                    changed = True
                    affected[name].update(found)
    # Reject an unexpected shared student record rather than erasing someone else's data.
    student_ids = affected['students']
    blockers = []
    for name, table in tables.items():
        if affected[name] and 'student_id' in table.c:
            shared = session.scalar(select(table.c.id).where(table.c.college_id == college,
                table.c.id.in_(sorted(affected[name])), table.c.student_id.not_in(sorted(student_ids))).limit(1))
            if shared is not None:
                blockers.append(name + ': shared student ownership')
        for fk in table.foreign_keys:
            target = fk.column
            if target.name != 'id' or not affected[target.table.name]:
                continue
            unowned = session.scalar(select(table.c.id).where(table.c.college_id == college,
                fk.parent.in_(sorted(affected[target.table.name])),
                table.c.id.not_in(sorted(affected[name]))).limit(1))
            if unowned is not None:
                blockers.append(name + '.' + fk.parent.name + ': retained shared reference')
    counts = {name: len(ids) for name, ids in sorted(affected.items())}
    fingerprint = hashlib.sha256(json.dumps({name: sorted(ids) for name, ids in sorted(affected.items())},
        sort_keys=True).encode()).hexdigest()
    result = {'college_id': college, 'user_id': identity, 'table_counts': counts,
        'plan_hash': fingerprint, 'blockers': sorted(set(blockers)), 'applied': False,
        'explanation': 'Database deletion only after a matching approved plan and expired restricted request. Shared references block execution. JSON/free-text references outside owned rows, hashed rate limits and external backups need recorded human review.'}
    return owner, affected, result

def plan(college, identity):
    if college < 1 or identity < 1:
        raise ValueError('Positive college and user identifiers required.')
    with tenant_session(college) as session:
        return _plan(session, college, identity)[2]

def erase(college, identity, approval):
    """Atomic deletion; approval is an explicit private owner-reviewed manifest."""
    required = ('plan_hash', 'approved_by', 'reason', 'backup_disposition', 'residual_identity_review')
    if any(not isinstance(approval.get(key), str) or not approval[key].strip() for key in required):
        raise ValueError('A complete owner-approved manifest is required.')
    with tenant_session(college) as session:
        # Same college-wide lock used for scheduling writes; no booking race during review.
        session.execute(text('SELECT pg_advisory_xact_lock(20260301, :college)'), {'college': college})
        owner, affected, result = _plan(session, college, identity)
        if approval['plan_hash'] != result['plan_hash'] or result['blockers']:
            raise ValueError('Plan changed or retained shared references require review.')
        request = session.scalar(select(DataRequest).where(DataRequest.college_id == college,
            DataRequest.user_id == identity, DataRequest.status == 'restricted_pending_erasure')
            .order_by(DataRequest.id.desc()).with_for_update())
        now = datetime.now(timezone.utc)
        if owner.disabled_at is None or request is None or request.retention_until is None or request.retention_until > now:
            raise ValueError('An expired restricted erasure request is required; retention cannot be bypassed.')
        # Break only nullable, owned cycles. No constraint or RLS is disabled.
        schedules = Base.metadata.tables['schedules']
        if affected['schedules']:
            session.execute(update(schedules).where(schedules.c.college_id == college,
                schedules.c.id.in_(sorted(affected['schedules']))).values(reschedule_interview_id=None))
        documents = Base.metadata.tables['offer_documents']
        if affected['offer_documents']:
            session.execute(update(documents).where(documents.c.college_id == college,
                documents.c.id.in_(sorted(affected['offer_documents']))).values(supersedes_document_id=None))
        # Delete leaves first, using FK dependencies rather than a hard-coded table order.
        pending = {name for name, ids in affected.items() if ids}
        while pending:
            leaves = []
            for name in pending:
                incoming = any(fk.column.table.name == name and fk.column.name == 'id'
                    and child_name != name and not (child_name == 'schedules' and fk.parent.name == 'reschedule_interview_id')
                    for child_name in pending for fk in Base.metadata.tables[child_name].foreign_keys)
                if not incoming:
                    leaves.append(name)
            if not leaves:
                raise ValueError('Unresolved dependency cycle; transaction rolled back.')
            for name in sorted(leaves):
                table = Base.metadata.tables[name]
                session.execute(delete(table).where(table.c.college_id == college, table.c.id.in_(sorted(affected[name]))))
                pending.remove(name)
        result.update(applied=True, erased_at=now.isoformat(), approval=approval,
            backup_erasure_completed=False,
            explanation='The approved owned database rows and private file bytes were erased atomically. External backup disposition remains separately recorded and is not certified by this receipt.')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--college', type=int, required=True)
    parser.add_argument('--user', type=int, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--approved-manifest', type=Path)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    if args.apply and (not args.approved_manifest or not args.receipt):
        parser.error('Explicit owner-approved manifest and private receipt path required for deletion.')
    try:
        if args.apply:
            # Reserve a writable receipt before any destructive transaction starts.
            with args.receipt.open('x', encoding='utf-8') as stream:
                approval = json.loads(args.approved_manifest.read_text(encoding='utf-8'))
                result = erase(args.college, args.user, approval)
                json.dump(result, stream, indent=2)
                stream.flush()
        else:
            result = plan(args.college, args.user)
            if args.receipt:
                with args.receipt.open('x', encoding='utf-8') as stream:
                    json.dump(result, stream, indent=2)
        print(json.dumps({key: value for key, value in result.items() if key != 'approval'}, indent=2))
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__}))
        raise SystemExit(1)
