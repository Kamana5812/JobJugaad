"""JobJugaad Phase 0 API: health check and development CORS."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from database import check_database
from schemas import HealthResponse

app = FastAPI(
    title="JobJugaad API",
    description="Explainability-first campus placement platform — Phase 0 skeleton.",
    version="0.0.1",
)

# Explicit Phase 0 setting; replace with the deployed frontend origin in Phase 5.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Report API availability and check PostgreSQL when configured."""
    try:
        database_status = check_database()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="The database is temporarily unavailable. Please try again shortly.",
        ) from None
    return HealthResponse(database=database_status)
