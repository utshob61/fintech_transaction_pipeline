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
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Try to create a rotating file handler in a writable location. Serverless
    # environments (like Vercel) have a read-only application directory, so
    # fall back to stdout if writing to disk is not possible.
    file_handler = None
    tried_paths = []
    for candidate in (Path("logs"), Path("/tmp/logs")):
        tried_paths.append(str(candidate))
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test_file = candidate / ".writetest"
            test_file.write_text("x")
            test_file.unlink(missing_ok=True)
            fh = logging.handlers.RotatingFileHandler(
                candidate / "app.log", maxBytes=5_000_000, backupCount=3
            )
            fh.setFormatter(formatter)
            file_handler = fh
            break
        except Exception:
            # Not writable — try next candidate
            file_handler = None

    root_logger = logging.getLogger()
    # Avoid adding duplicate handlers if this is called multiple times
    if root_logger.handlers:
        return

    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)
    else:
        root_logger.warning(
            "File logging disabled; no writable log directory found (tried: %s)",
            tried_paths,
        )
