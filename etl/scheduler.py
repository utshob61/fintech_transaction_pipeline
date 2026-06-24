"""
scheduler.py
------------
Optional scheduled-job runner using APScheduler.

In a real deployment you would either:
  (a) run this as a long-lived process (e.g. a 4th Docker service), or
  (b) replace it with your platform's native cron (Render Cron Jobs,
      Railway Cron, GitHub Actions schedule, etc.) calling
      `python -m etl.pipeline --csv ...` on a timer.

This file demonstrates option (a): it watches a folder (data/incoming/)
and runs the ETL pipeline on any new CSV files dropped there, on a
configurable interval.

Run with:
    python -m etl.scheduler
"""

import logging
import os
import shutil
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from sqlalchemy import create_engine

from etl.pipeline import run_pipeline_from_csv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fintech_user:fintech_pass@localhost:5432/fintech_db")
INCOMING_DIR = Path("data/incoming")
PROCESSED_DIR = Path("data/processed")
RUN_EVERY_MINUTES = int(os.getenv("ETL_SCHEDULE_MINUTES", 10))

engine = create_engine(DATABASE_URL)


def process_incoming_files():
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = list(INCOMING_DIR.glob("*.csv"))
    if not csv_files:
        logger.info("No new files in %s.", INCOMING_DIR)
        return

    for file_path in csv_files:
        logger.info("Processing scheduled file: %s", file_path)
        try:
            report = run_pipeline_from_csv(str(file_path), engine)
            logger.info("Done: %s -> %s", file_path.name, report)
            shutil.move(str(file_path), PROCESSED_DIR / file_path.name)
        except Exception:
            logger.exception("Failed to process %s", file_path)


def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(process_incoming_files, "interval", minutes=RUN_EVERY_MINUTES)
    logger.info("Scheduler started. Checking every %d minutes.", RUN_EVERY_MINUTES)
    process_incoming_files()  # run once immediately on startup
    scheduler.start()


if __name__ == "__main__":
    main()
