"""Encrypted, explicitly scoped tenant snapshots; restore only into an empty local drill database."""
import argparse
import base64
import hashlib
import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID
from cryptography.fernet import Fernet
from sqlalchemy import Date, DateTime, LargeBinary, Numeric, Uuid, insert, select, text, update
from sqlalchemy.orm import Session
from database import Base, engine, initialize_schema, tenant_session
from security_audit import require_isolation
import models

def encode(value):
    if isinstance(value,bytes): return base64.b64encode(value).decode('ascii')
    if isinstance(value,datetime): return value.astimezone(timezone.utc).isoformat()
    if isinstance(value,(date,Decimal,UUID)): return str(value)
    return value

def decode(column,value):
    if value is None: return None
    if isinstance(column.type,LargeBinary): return base64.b64decode(value,validate=True)
    if isinstance(column.type,DateTime): return datetime.fromisoformat(value)
    if isinstance(column.type,Date): return date.fromisoformat(value)
    if isinstance(column.type,Numeric): return Decimal(value)
    if isinstance(column.type,Uuid) and column.type.as_uuid: return UUID(value)
    return value

def snapshot(colleges):
    with engine.connect() as connection: require_isolation(connection)
    tenants={}
    for college in colleges:
        # Repeatable-read per tenant, explicit application filters plus FORCE RLS.
        with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection:
            with Session(bind=connection) as session, session.begin():
                session.execute(text("SELECT set_config('app.college_id', :tenant, true)"),{'tenant':str(college)})
                tenants[str(college)]={table.name:[{k:encode(v) for k,v in row.items()} for row in
                    session.execute(select(table).where(table.c.college_id==college).order_by(table.c.id)).mappings()]
                    for table in Base.metadata.sorted_tables}
    return {'format':1,'created_at':datetime.now(timezone.utc).isoformat(),'colleges':colleges,'tenants':tenants}

def digest(tenants):
    return hashlib.sha256(json.dumps(tenants,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def backup(path,colleges):
    key=os.environ.get('BACKUP_ENCRYPTION_KEY','')
    payload=snapshot(colleges)
    blob=Fernet(key.encode()).encrypt(json.dumps(payload,separators=(',',':')).encode())
    with Path(path).open('xb') as file: file.write(blob)
    return {'encrypted_sha256':hashlib.sha256(blob).hexdigest(),'rows':sum(len(r) for t in payload['tenants'].values() for r in t.values()),'tables':len(Base.metadata.tables),
        'source_digest':digest(payload['tenants']),'coverage':'Listed tenants only; no production/global backup completeness claim.'}

def restore(path):
    if os.environ.get('ALLOW_RESTORE_DATABASE')!='yes' or engine.url.host not in ('127.0.0.1','localhost') or not engine.url.database.startswith('jobjugaad_restore_'):
        raise RuntimeError('Explicitly authorized, empty local jobjugaad_restore_ database required.')
    payload=json.loads(Fernet(os.environ['BACKUP_ENCRYPTION_KEY'].encode()).decrypt(Path(path).read_bytes()))
    if payload.get('format')!=1 or not payload['colleges'] or any(type(c) is not int or c<1 for c in payload['colleges']): raise RuntimeError('Unsupported snapshot.')
    initialize_schema()
    from colleges import COLLEGES
    for college in set(COLLEGES)|set(payload['colleges']):
        with tenant_session(college) as session:
            if any(session.scalar(select(t.c.id).where(t.c.college_id==college).limit(1)) is not None for t in Base.metadata.sorted_tables):
                raise RuntimeError('Nonempty target: no rows will be overwritten.')
    for college in payload['colleges']:
        tables=payload['tenants'][str(college)]
        if set(tables)!=set(Base.metadata.tables): raise RuntimeError('Snapshot schema mismatch.')
        for name,rows in tables.items():
            if any(set(r)!=set(Base.metadata.tables[name].columns.keys()) or type(r['college_id']) is not int or r['college_id']!=college for r in rows):
                raise RuntimeError('Snapshot tenant/column mismatch.')
    with engine.begin() as connection:
        reschedule_links=[]
        for table in Base.metadata.sorted_tables:
            maximum=0
            for college in payload['colleges']:
                connection.execute(text("SELECT set_config('app.college_id', :tenant, true)"),{'tenant':str(college)})
                for row in payload['tenants'][str(college)][table.name]:
                    values={c.name:decode(c,row[c.name]) for c in table.columns}
                    # The optional reschedule FK forms a schedule/interview
                    # cycle. Stage only this nullable link; preserve every
                    # constraint and reconnect inside the same transaction.
                    if table.name=='schedules' and values['reschedule_interview_id'] is not None:
                        reschedule_links.append((college,row['id'],values['reschedule_interview_id']))
                        values['reschedule_interview_id']=None
                    connection.execute(insert(table).values(**values))
                    maximum=max(maximum,row['id'])
            # Trusted ORM table names; sequence repair is documented maintenance SQL.
            if maximum: connection.execute(text("SELECT setval(pg_get_serial_sequence(:table, 'id'), :value, true)"),{'table':table.name,'value':maximum})
        schedules=Base.metadata.tables['schedules']
        for college,identity,interview in reschedule_links:
            connection.execute(text("SELECT set_config('app.college_id', :tenant, true)"),{'tenant':str(college)})
            connection.execute(update(schedules).where(schedules.c.college_id==college,schedules.c.id==identity)
                .values(reschedule_interview_id=interview))
    actual=snapshot(payload['colleges'])
    if digest(actual['tenants'])!=digest(payload['tenants']): raise RuntimeError('Restored row/byte comparison failed.')
    return {'verified':True,'tables':len(Base.metadata.tables),'rows':sum(len(r) for t in actual['tenants'].values() for r in t.values()),'source_digest':digest(payload['tenants']),'policies':'verified'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['backup','restore-drill'])
    parser.add_argument('--path',required=True);parser.add_argument('--colleges')
    args=parser.parse_args()
    try:
        if args.action=='backup':
            colleges=sorted(set(int(c) for c in (args.colleges or '').split(',') if c))
            if not colleges or any(c<1 for c in colleges): raise RuntimeError('Explicit authorized colleges required.')
            result=backup(args.path,colleges)
        else: result=restore(args.path)
        print(json.dumps(result,indent=2))
    except Exception as error:
        # Never log credentials, URLs, keys, decrypted records or driver error details.
        original=getattr(error,'orig',None)
        diagnostic=getattr(original,'diag',None)
        print(json.dumps({'status':'failed','error_type':type(error).__name__,
            'sqlstate':getattr(original,'pgcode',None),
            'constraint':getattr(diagnostic,'constraint_name',None),
            'table':getattr(diagnostic,'table_name',None)}));raise SystemExit(1)
