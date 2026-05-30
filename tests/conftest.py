"""
Pytest shared fixtures.

Provides:
    - In-memory SQLite database for fast, isolated tests
    - Pre-configured DB session
    - FastAPI TestClient
    - Sample data factories
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from store_intel.db.models import Base
from store_intel.db.engine import get_db
from store_intel.main import app


# ── In-Memory SQLite Engine ─────────────────────────────────
# StaticPool ensures all connections share the same in-memory database.
# Without it, each connection to "sqlite://" gets a separate empty DB.
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@sa_event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ── Fixtures ────────────────────────────────────────────────


@pytest.fixture(scope="function")
def db_session():
    """
    Provide a clean database session for each test.

    Creates all tables before the test, drops them after.
    """
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Provide a FastAPI TestClient with the test database injected.

    The dependency override ensures ALL request-scoped db sessions
    use the same in-memory test session (which has tables created).
    """

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    # Use raise_server_exceptions=True so test failures are clear
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_store(db_session):
    """Create a sample store in the test database."""
    from store_intel.db.models import Store

    store = Store(store_id="test_store_001", name="Test Store")
    db_session.add(store)
    db_session.commit()
    return store


@pytest.fixture
def sample_visitor(db_session, sample_store):
    """Create a sample visitor in the test database."""
    from store_intel.db.models import Visitor

    visitor = Visitor(visitor_id="v_test_001", store_id=sample_store.store_id)
    db_session.add(visitor)
    db_session.commit()
    return visitor
