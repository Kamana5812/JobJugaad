from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# Import routers and DB utilities
from routers import auth as auth_router
from routers import students as students_router
from database import Base, engine

app = FastAPI()

# CORS configuration – allow the Vercel frontend origin (or all in dev)
origins = [os.getenv("FRONTEND_ORIGIN", "*")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from routers import recruiter as recruiter_router

# Include API routers
app.include_router(auth_router.router, prefix="/auth")
app.include_router(students_router.router, prefix="/students")
app.include_router(recruiter_router.router, prefix="/recruiter")


# Create DB tables on startup (useful for SQLite dev)
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

