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

    Raw SQL is used only for PostgreSQL policy DDL, catalog checks and session
    settings, which SQLAlchemy's portable metadata API does not represent.
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
        for table in Base.metadata.sorted_tables:
            name = connection.dialect.identifier_preparer.quote(table.name)
            connection.execute(text(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY"))
            connection.execute(text(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY"))
            exists = connection.execute(text("SELECT 1 FROM pg_policies WHERE schemaname = current_schema() AND tablename = :table AND policyname = 'college_isolation'"), {"table": table.name}).scalar()
            if not exists:
                predicate = "college_id = NULLIF(current_setting('app.college_id', true), '')::integer"
                connection.execute(text(f"CREATE POLICY college_isolation ON {name} USING ({predicate}) WITH CHECK ({predicate})"))

def check_database():
    if SessionLocal is None:
        return "not_configured"
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return "connected"
