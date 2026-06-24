"""
pipeline.py
-----------
Orchestrates the full ETL pipeline: Extract -> Transform -> Fraud-flag -> Load.

Can be used:
  1. As a CLI script:      python -m etl.pipeline --csv data/sample_transactions.csv
  2. Imported by FastAPI:  run_pipeline_from_csv(path, engine)
  3. Imported by scheduler.py for periodic batch jobs.
"""

import argparse
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from etl.extract import extract_from_api, extract_from_csv, extract_from_json_records
from etl.fraud_detection import flag_suspicious_transactions
from etl.load import load_to_postgres
from etl.transform import clean_transactions

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fintech_user:fintech_pass@localhost:5432/fintech_db")


def _run(df, engine) -> dict:
    """Shared transform -> fraud -> load logic used by every entry point."""
    clean_df, transform_report = clean_transactions(df)
    flagged_df = flag_suspicious_transactions(clean_df)
    load_report = load_to_postgres(flagged_df, engine)

    return {**transform_report, **load_report, "suspicious_flagged": int(flagged_df["is_suspicious"].sum())}


def run_pipeline_from_csv(file_path: str, engine=None) -> dict:
    engine = engine or create_engine(DATABASE_URL)
    df = extract_from_csv(file_path)
    return _run(df, engine)


def run_pipeline_from_api(api_url: str, engine=None) -> dict:
    engine = engine or create_engine(DATABASE_URL)
    df = extract_from_api(api_url)
    return _run(df, engine)


def run_pipeline_from_records(records: list, engine=None) -> dict:
    """Used by the FastAPI JSON-ingestion endpoint."""
    engine = engine or create_engine(DATABASE_URL)
    df = extract_from_json_records(records)
    return _run(df, engine)


def main():
    parser = argparse.ArgumentParser(description="Run the fintech ETL pipeline manually.")
    parser.add_argument("--csv", help="Path to a transactions CSV file.")
    parser.add_argument("--api", help="URL of a JSON transactions API to pull from.")
    args = parser.parse_args()

    if not args.csv and not args.api:
        parser.error("Provide --csv <path> or --api <url>.")

    engine = create_engine(DATABASE_URL)

    if args.csv:
        report = run_pipeline_from_csv(args.csv, engine)
    else:
        report = run_pipeline_from_api(args.api, engine)

    logger.info("Pipeline finished. Report: %s", report)


if __name__ == "__main__":
    main()
