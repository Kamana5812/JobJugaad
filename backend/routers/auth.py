from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
import models, schemas, auth


router = APIRouter()

@router.post("/signup", response_model=schemas.Token)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Create user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, password_hash=hashed_password, role=user.role)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    # Create associated profile based on role
    if user.role == "student":
        student = models.Student(
            user_id=db_user.id,
            name=user.name,
            branch=user.branch,
            cgpa=user.cgpa,
            backlog_count=0,
            aptitude_score=0.0,
            communication_score=0.0,
            interview_score=0.0,
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)
    # Issue JWT token (subject = email)
    access_token = auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
async def login(credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == credentials.email))
    user = result.scalar_one_or_none()
    if not user or not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
