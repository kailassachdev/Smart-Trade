"""
database.py
-----------
Database engine configuration. 
Reads DATABASE_URL from environment — supports both SQLite (dev) and PostgreSQL (prod).

ARCHITECTURAL IMPROVEMENT #1: Scalable Database Design
- Uses connection pooling (pool_size, max_overflow, pool_pre_ping) for production
- SQLite fallback automatically disables pooling (NullPool), which is required for SQLite
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./smarttrade.db"   # Default: SQLite for development
)

IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    # SQLite requires check_same_thread=False and cannot use connection pooling
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,  # No pooling for SQLite
    )
else:
    # PostgreSQL: production-grade connection pool settings
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,          # Number of persistent connections in the pool
        max_overflow=20,       # Extra connections allowed above pool_size under load
        pool_pre_ping=True,    # Verify connections are alive before using them (handles disconnections)
        pool_recycle=3600,     # Recycle connections after 1 hour to avoid stale connections
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and ensures it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
