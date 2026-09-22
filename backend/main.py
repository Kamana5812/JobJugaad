"""JobJugaad API: explainability-first student core."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from auth import signing_secret
from database import check_database, initialize_schema
from routers import auth, students, recruiters
from schemas import HealthResponse
from seed import seed_students, seed_companies

@asynccontextmanager
async def lifespan(app):
    signing_secret()
    initialize_schema()  # Tables and FORCE RLS are committed atomically before serving.
    created = seed_students()
    companies, demonstrations = seed_companies()
    logging.getLogger("uvicorn.error").info("Phase 2 FORCE RLS initialized; created %s students, %s companies; new drive demonstrations: %s", created, companies, demonstrations)
    yield

app = FastAPI(title="JobJugaad API", version="0.3.0",
    description="Explainability-first Student Core and Talent Finder. Proposed weighted rules; no trained model.",
    lifespan=lifespan)
# Explicit Phase 0/1 setting; restrict allowed origins in Phase 5.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(recruiters.router)

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    messages = [f"{'.'.join(str(p) for p in item['loc'] if p != 'body')}: {item['msg']}" for item in error.errors()]
    return JSONResponse(status_code=422, content={"detail": "Please check your input. " + "; ".join(messages)})

@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, error: SQLAlchemyError):
    logging.getLogger("jobjugaad").error("Database operation failed (%s)", type(error).__name__)
    return JSONResponse(status_code=503, content={"detail": "The database is temporarily unavailable. Please try again."})

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    try:
        return HealthResponse(database=check_database())
    except SQLAlchemyError:
        raise HTTPException(503, "The database is temporarily unavailable.") from None
