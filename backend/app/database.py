"""
Database configuration and SQLite connection setup for AegisAPI.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default SQLite database path (configurable via environment variables in future)
SQLALCHEMY_DATABASE_URL = "sqlite:///./aegis_api.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite in multi-threaded FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session per request
    and ensures proper teardown.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

