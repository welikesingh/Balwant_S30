"""Logging helper. Writes every success and failure to a log file."""

import logging
import sys
from pathlib import Path

LOG_FILE = Path(__file__).parent / "organizer.log"


def setup_logger() -> logging.Logger:
    """Create (or reuse) a logger that writes to organizer.log."""
    logger = logging.getLogger("file_organizer")

    # if this logger is already set up, don’t set it up again — just return it.
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also print messages in the terminal so a beginner can see what happened.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def log_success(logger: logging.Logger, message: str) -> None:
    logger.info(message)


def log_failure(logger: logging.Logger, message: str) -> None:
    logger.error(message)
