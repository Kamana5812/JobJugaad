"""Minimal FastAPI app with health endpoint and permissive CORS for Phase 0.

The CORS policy is wide‑open (allow_all_origins=True) as a placeholder – it will be locked down later in Phase 5.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Wide‑open CORS for initial development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict:
    """Simple health check used by the frontend landing page.
    Returns a JSON payload confirming the service is up.
    """
    return {"status": "ok"}
