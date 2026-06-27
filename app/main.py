from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db
from .schemas import UserCreate, UserResponse, TaskResponse, Token
from .models import User, DocumentTask
from .tasks import process_document
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Document Processing Pipeline")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str, db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=Token)
def login(user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/upload", response_model=TaskResponse)
async def upload_document(
    token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user(token, db)
    content = await file.read()
    content_str = content.decode("utf-8")

    task = DocumentTask(
        user_id=current_user.id,
        file_name=file.filename,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    process_document.delay(task.id, content_str)

    return task


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    task = db.query(DocumentTask).filter(
        DocumentTask.id == task_id,
        DocumentTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/tasks", response_model=list[TaskResponse])
def get_all_tasks(token: str, db: Session = Depends(get_db)):
    current_user = get_current_user(token, db)
    return db.query(DocumentTask).filter(
        DocumentTask.user_id == current_user.id
    ).all()