'''Database connection and session handling for FastAPI.

- `DATABASE_URL` is read from the Render environment variable.
- `engine` is created with SQLAlchemy 2.x style.
- `SessionLocal` provides a scoped session for request handlers.
- `Base` is the declarative base for all ORM models.
'''

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

# Use future engine (SQLAlchemy 2.x) and echo off for production.
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
