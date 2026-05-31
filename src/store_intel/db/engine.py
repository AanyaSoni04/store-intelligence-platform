"""
SQLAlchemy engine and session factory.

Provides:
- `engine`: the SQLAlchemy Engine instance
- `SessionLocal`: a sessionmaker bound to the engine
- `get_db()`: FastAPI dependency yielding a session per request
- `init_db()`: creates all tables (called at startup)
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from store_intel.config import settings

# ── Engine ──────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    # SQLite-specific: allow same connection across threads (FastAPI uses threadpool)
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
)

# Enable foreign keys for SQLite (Journal mode PRAGMA removed due to WSL volume mount I/O errors)
if "sqlite" in settings.database_url:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


# ── Session factory ─────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Usage in route:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables defined in models.py.

    Called once at application startup.
    """
    from store_intel.db.models import Base  # noqa: F811 — imported here to avoid circular deps

    Base.metadata.create_all(bind=engine)
