from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from database import engine, Base
from routers import auth, students, recruiters

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="JobJugaad API")

# Allow CORS for the frontend
origins = [
    "http://localhost:5173",
    "https://job-jugaad-sepia.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(recruiters.router)

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "ok"})

