"""Optional PostgreSQL connection for the Phase 0 deployment health check."""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = (
    create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
    if database_url
    else None
)
SessionLocal = sessionmaker(bind=engine) if engine is not None else None


def check_database() -> str:
    """Check connectivity without creating tables or accessing tenant data."""
    if SessionLocal is None:
        return "not_configured"
    with SessionLocal() as session:
        # SELECT 1 is a connection probe, not a tenant-table query.
        session.execute(text("SELECT 1"))
    return "connected"
