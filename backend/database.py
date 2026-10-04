"""PostgreSQL sessions and atomic schema/RLS initialization."""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5}) if database_url else None
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False) if engine is not None else None

@contextmanager
def tenant_session(college_id: int):
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured for Student Core.")
    with SessionLocal.begin() as session:
        # Transaction-local tenant setting is cleared on commit/rollback and pool reuse.
        session.execute(text("SELECT set_config('app.college_id', :tenant, true)"), {"tenant": str(college_id)})
        yield session

def initialize_schema():
    """Create tables and FORCE RLS in one transaction before accepting requests.

    Raw SQL is used only for PostgreSQL policy DDL, catalog checks, session
    settings and additive schema upgrades. create_all does not add columns to
    existing tables, so IF NOT EXISTS upgrades preserve every legacy booking
    and proposal with explicit round-one/empty-evidence defaults.
    Application data queries use SQLAlchemy and explicit college_id filters.
    """
    import models  # register Phase 1 tables
    if engine is None or engine.dialect.name != "postgresql":
        raise RuntimeError("Student Core requires PostgreSQL with RLS.")
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(20260101)"))
        if connection.execute(text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user")).scalar_one():
            raise RuntimeError("Database runtime role must not be superuser or BYPASSRLS.")
        Base.metadata.create_all(connection)
        connection.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version integer NOT NULL DEFAULT 0'))
        for name in ("schedules", "interviews"):
            connection.execute(text(f"ALTER TABLE {name} ADD COLUMN IF NOT EXISTS round_number integer NOT NULL DEFAULT 1"))
            connection.execute(text(f"ALTER TABLE {name} ADD COLUMN IF NOT EXISTS round_name varchar(80) NOT NULL DEFAULT 'Interview'"))
            check_name = f"ck_{name}_round_number"
            exists = connection.execute(text("SELECT 1 FROM pg_constraint WHERE conrelid = CAST(:table AS regclass) AND conname = :name"),
                {"table": name, "name": check_name}).scalar()
            if not exists:
                connection.execute(text(f"ALTER TABLE {name} ADD CONSTRAINT {check_name} CHECK (round_number BETWEEN 1 AND 20)"))
        connection.execute(text("ALTER TABLE schedules ADD COLUMN IF NOT EXISTS calendar_conflicts json NOT NULL DEFAULT '[]'::json"))
        for table in Base.metadata.sorted_tables:
            name = connection.dialect.identifier_preparer.quote(table.name)
            connection.execute(text(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY"))
            connection.execute(text(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY"))
            exists = connection.execute(text("SELECT 1 FROM pg_policies WHERE schemaname = current_schema() AND tablename = :table AND policyname = 'college_isolation'"), {"table": table.name}).scalar()
            if not exists:
                predicate = "college_id = NULLIF(current_setting('app.college_id', true), '')::integer"
                connection.execute(text(f"CREATE POLICY college_isolation ON {name} USING ({predicate}) WITH CHECK ({predicate})"))

        from security_audit import require_isolation
        require_isolation(connection)

def isolation_report():
    from security_audit import require_isolation
    if engine is None:
        raise RuntimeError("Database is not configured.")
    with engine.connect() as connection:
        return require_isolation(connection)

def check_database():
    if SessionLocal is None:
        return "not_configured"
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return "connected"
