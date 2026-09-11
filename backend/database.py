import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Depends

# Default to SQLite for local development; Render will provide a PostgreSQL URL via DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# Dependency to get an async DB session for FastAPI endpoints.
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
