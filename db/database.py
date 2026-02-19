"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from pathlib import Path

from db.models import Base
from config.settings import get_settings


def get_engine():
    """Create database engine with proper configuration."""
    settings = get_settings()

    # Ensure data directory exists
    db_path = settings.database_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=settings.debug
    )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables. Use with caution!"""
    Base.metadata.drop_all(bind=engine)


@contextmanager
def get_db_context() -> Session:
    """Database session context manager for scripts and CLI."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
