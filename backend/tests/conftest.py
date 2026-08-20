import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base


@pytest.fixture()
def db_session():
    """A fresh in-memory SQLite DB per test, with all tables created.

    This is a disposable local test database — never the shared Supabase
    instance. Portable column types (String UUIDs, JSON lists) let the same
    models run identically here and against Postgres in production.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    import app.models  # noqa: F401  ensures all model classes are registered on Base

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session: Session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client():
    """A TestClient wired to its own in-memory SQLite DB (shared across all
    requests made within one test via StaticPool), overriding the app's
    get_db dependency. Used for API-layer tests."""
    from app.database.session import get_db
    from app.main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app import models  # noqa: F401  registers all model classes on Base; avoids rebinding `app`

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
