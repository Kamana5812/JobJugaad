"""JobJugaad API: explainability-first student core."""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from auth import signing_secret
from database import check_database, initialize_schema, isolation_report
from routers import auth, students, recruiters, admin, notifications, announcements, offer_documents, privacy
from upload_limits import DocumentUploadLimitMiddleware
from schemas import HealthResponse
from engines.placement_model import load_model, model_status
from engines import btech_model
from seed import seed_students, seed_companies, seed_phase3, seed_phase4
from admin_access import provision_admin_accounts

@asynccontextmanager
async def lifespan(app):
    signing_secret()
    load_model()
    btech_model.load_model()
    initialize_schema()  # Tables and FORCE RLS are committed atomically before serving.
    # Real deployments do not create synthetic tenants or workflow records.
    if os.environ.get("SEED_DEMO_DATA") == "yes":
        seed_students(); seed_companies(); seed_phase3(); seed_phase4()
    admins = provision_admin_accounts()
    logging.getLogger("uvicorn.error").info("Tenant RLS initialized; admin accounts provisioned: %s", admins)
    yield

app = FastAPI(title="JobJugaad API", version="0.18.0",
    description="Explainability-first Student Core, Talent Finder and Placement Command Center. Weighted rules plus separate public-data engineering and MBA Random Forest placement signals.",
    lifespan=lifespan)
# Exact production origin. CORS is a browser boundary, not a substitute for JWT/RBAC/RLS.
# Added first so CORS wraps even early upload-limit/authentication responses.
app.add_middleware(DocumentUploadLimitMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["https://jobjugaad.vercel.app"], allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(recruiters.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(announcements.router)
app.include_router(offer_documents.router)
app.include_router(privacy.router)

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
        return HealthResponse(database=check_database(), isolation=isolation_report(), placement_model=model_status(), btech_model=btech_model.model_status())
    except (SQLAlchemyError, RuntimeError):
        raise HTTPException(503, "The database health or isolation check failed.") from None

from colleges import DIRECTORY
from schemas import CollegeDirectory

@app.get("/colleges", response_model=CollegeDirectory, tags=["College directory"])
def colleges():
    return DIRECTORY
