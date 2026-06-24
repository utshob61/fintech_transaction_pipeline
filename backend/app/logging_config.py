"""
logging_config.py
------------------
Centralized logging setup. Imported once from main.py so every module
(ETL, routers, etc.) shares the same console + rotating-file handlers.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log", maxBytes=5_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
