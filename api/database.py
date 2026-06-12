# api/database.py
# Handles all database connections and session management
# Connects to Supabase PostgreSQL using SQLAlchemy

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL:
    raise ValueError("SUPABASE_DB_URL not found in .env file")

# Create SQLAlchemy engine
# pool_pre_ping=True automatically reconnects dropped connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping    = True,
    pool_size        = 5,
    max_overflow     = 10,
    connect_args     = {"connect_timeout": 10}
)

# Session factory — used in every route via get_db()
SessionLocal = sessionmaker(
    autocommit = False,
    autoflush  = False,
    bind       = engine
)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session per request,
    closes it automatically when the request is done.
    Usage in routes: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection():
    """
    Called at app startup to verify DB is reachable.
    Returns True if connected, raises exception if not.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}")