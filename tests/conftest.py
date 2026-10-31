import os

os.environ.setdefault("API_KEY", "test-api-key")
os.environ.pop("REDIS_URL", None)

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.rate_limit import reset_rate_limiter


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    reset_rate_limiter()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    reset_rate_limiter()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def auth_headers():
    return {
        "X-API-Key": os.getenv(
            "API_KEY",
            "test-api-key",
        )
    }
