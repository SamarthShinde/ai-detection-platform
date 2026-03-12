"""Shared pytest fixtures for the test suite."""
import io
import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base
from app.utils.db import get_db

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test.db file
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="function")
def db():
    """Return a fresh DB session, rolling back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def client():
    """Return a TestClient with DB override and rate-limit bypass applied."""
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    # Bypass Redis rate-limiting in tests so repeated calls don't trigger 429
    with patch(
        "app.services.rate_limit_service.rate_limit_service.check_rate_limit",
        return_value=(True, {"requests_per_minute": 999, "remaining_minute": 999}),
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    app.dependency_overrides.clear()


# ── Helper factories ──────────────────────────────────────────────────────────

def make_png_bytes(width: int = 8, height: int = 8) -> bytes:
    """Return a minimal valid PNG file as bytes."""
    try:
        from PIL import Image
        img = Image.new("RGB", (width, height), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimal 1×1 red PNG (hardcoded)
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )


@pytest.fixture
def png_file():
    return make_png_bytes()


@pytest.fixture
def registered_user(client):
    """Register + verify + login a test user; returns token + user info."""
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"

    # Register
    r = client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Test User"
    })
    assert r.status_code in (200, 201), r.text

    # Get OTP from DB
    db = TestingSessionLocal()
    from app.models.database import User
    user = db.query(User).filter(User.email == email).first()

    # Force-verify without OTP (shortcut for tests)
    from datetime import datetime
    user.is_verified = True
    user.verified_at = datetime.utcnow()
    db.commit()
    user_id = user.id
    db.close()

    # Login
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    return {"token": token, "email": email, "user_id": user_id, "password": password}
