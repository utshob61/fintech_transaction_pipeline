"""
init_db.py
----------
Standalone script that (re)creates the PostgreSQL schema from schema.sql.

Usage:
    python database/init_db.py

It is also safe to import `init_database()` from elsewhere (e.g. FastAPI's
startup event) since CREATE TABLE statements use IF NOT EXISTS.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fintech_user:fintech_pass@localhost:5432/fintech_db")
SCHEMA_FILE = Path(__file__).parent / "schema.sql"


def init_database(database_url: str = DATABASE_URL) -> None:
    """Execute schema.sql against the target database."""
    logger.info("Connecting to database to apply schema...")
    engine = create_engine(database_url)

    sql_script = SCHEMA_FILE.read_text()

    with engine.begin() as conn:
        # Split on semicolons so we can run each statement separately
        # (psycopg2/SQLAlchemy don't always like multi-statement strings).
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))

    logger.info("Schema applied successfully.")


if __name__ == "__main__":
    init_database()
