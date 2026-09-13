'''Authentication routes: signup and login, issuing JWTs.
- Passwords are hashed with PassLib (bcrypt).
- JWT payload includes `user_id`, `role`, and `college_id`.
- Tokens are signed with the `JWT_SECRET` env variable.
'''

import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import SessionLocal, engine
from .. import models, schemas

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day token lifetime

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/signup", response_model=schemas.UserRead)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Ensure email uniqueness
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = models.User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        role=user.role,
        college_id=user.college_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token_data = {
        "user_id": str(user.id),
        "role": user.role,
        "college_id": str(user.college_id),
    }
    access_token = create_access_token(token_data)
    return {"access_token": access_token}
