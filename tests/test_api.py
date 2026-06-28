import os

# Must be set before any app module is imported so database.py resolves env vars
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_placeholder.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

# Patch app.database before app.main is imported so the in-memory engine is
# used everywhere (including the create_all call inside app.main).
import app.database as _db

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
_db.engine = _test_engine
_db.SessionLocal = _TestSession

from app import models

models.Base.metadata.create_all(bind=_test_engine)

from app.main import app


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[_db.get_db] = _override_get_db

client = TestClient(app)


def test_register():
    resp = client.post(
        "/register",
        json={"username": "reg_user_1", "email": "reg_user_1@test.com", "password": "pass1234"},
    )
    assert resp.status_code == 200
    assert "id" in resp.json()


def test_login():
    client.post(
        "/register",
        json={"username": "login_user_1", "email": "login_user_1@test.com", "password": "pass1234"},
    )
    resp = client.post(
        "/login",
        json={"username": "login_user_1", "password": "pass1234"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_upload_requires_auth():
    import io

    resp = client.post(
        "/upload",
        files={"file": ("doc.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    # HTTPBearer in this FastAPI/Starlette version returns 401 for missing credentials
    assert resp.status_code in (401, 403)
