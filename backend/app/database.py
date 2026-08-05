"""
database.py
-----------
SQLAlchemy engine/session setup shared by the whole backend.
"""

import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
FALLBACK_DATABASE_URL = "sqlite:///:memory:"

sqlite_engine_kwargs = {
    "connect_args": {"check_same_thread": False},
    "poolclass": StaticPool,
}

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logging.warning("Remote DATABASE_URL is unreachable; using SQLite fallback database.")
        DATABASE_URL = FALLBACK_DATABASE_URL
        engine = create_engine(DATABASE_URL, **sqlite_engine_kwargs)
else:
    DATABASE_URL = FALLBACK_DATABASE_URL
    engine = create_engine(DATABASE_URL, **sqlite_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
