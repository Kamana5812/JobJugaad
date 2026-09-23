"""JobJugaad API: explainability-first student core."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from auth import signing_secret
from database import check_database, initialize_schema, isolation_report
from routers import auth, students, recruiters, admin, notifications
from schemas import HealthResponse
from seed import seed_students, seed_companies, seed_phase3, seed_phase4
from admin_access import provision_admin_accounts

@asynccontextmanager
async def lifespan(app):
    signing_secret()
    initialize_schema()  # Tables and FORCE RLS are committed atomically before serving.
    created = seed_students()
    companies, demonstrations = seed_companies()
    logging.getLogger("uvicorn.error").info("Phase 2 FORCE RLS initialized; created %s students, %s companies; new drive demonstrations: %s", created, companies, demonstrations)
    phase3 = seed_phase3()
    phase4 = seed_phase4()
    logging.getLogger("uvicorn.error").info("Phase 4 FORCE RLS initialized; synthetic expansion: %s", phase4)
    admins = provision_admin_accounts()
    logging.getLogger("uvicorn.error").info("Phase 3 FORCE RLS initialized; fixtures: %s; admin accounts provisioned: %s", phase3, admins)
    yield

app = FastAPI(title="JobJugaad API", version="0.6.0",
    description="Explainability-first Student Core, Talent Finder and Placement Command Center. Proposed weighted rules; no trained model.",
    lifespan=lifespan)
# Exact production origin. CORS is a browser boundary, not a substitute for JWT/RBAC/RLS.
app.add_middleware(CORSMiddleware, allow_origins=["https://jobjugaad.vercel.app"], allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(recruiters.router)
app.include_router(admin.router)
app.include_router(notifications.router)

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
        return HealthResponse(database=check_database(), isolation=isolation_report())
    except (SQLAlchemyError, RuntimeError):
        raise HTTPException(503, "The database health or isolation check failed.") from None
