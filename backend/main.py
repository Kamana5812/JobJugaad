"""Minimal FastAPI app with health endpoint and permissive CORS for Phase 0.

The CORS policy is wide‑open (allow_all_origins=True) as a placeholder – it will be locked down later in Phase 5.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

from .routers import auth, students
app.include_router(auth.router)
app.include_router(students.router)

# Wide‑open CORS for initial development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Create tables if they don't exist
    from .database import engine, Base
    Base.metadata.create_all(bind=engine)
    # Enable Row‑Level Security and create policies for multi‑tenant tables
    from sqlalchemy import text
    from .database import SessionLocal
    db = SessionLocal()
    try:
        policies = [
            "ALTER TABLE users ENABLE ROW LEVEL SECURITY;",
            "CREATE POLICY users_college_policy ON users USING (college_id = current_setting('app.college_id')::uuid);",
            "ALTER TABLE students ENABLE ROW LEVEL SECURITY;",
            "CREATE POLICY students_college_policy ON students USING (college_id = current_setting('app.college_id')::uuid);",
            "ALTER TABLE student_skills ENABLE ROW LEVEL SECURITY;",
            "CREATE POLICY skills_college_policy ON student_skills USING (college_id = current_setting('app.college_id')::uuid);",
            "ALTER TABLE projects ENABLE ROW LEVEL SECURITY;",
            "CREATE POLICY projects_college_policy ON projects USING (college_id = current_setting('app.college_id')::uuid);",
            "ALTER TABLE certifications ENABLE ROW LEVEL SECURITY;",
            "CREATE POLICY certs_college_policy ON certifications USING (college_id = current_setting('app.college_id')::uuid);",
        ]
        for stmt in policies:
            db.execute(text(stmt))
        db.commit()
    finally:
        db.close()

    """Simple health check used by the frontend landing page.
    Returns a JSON payload confirming the service is up.
    """
    return {"status": "ok"}
