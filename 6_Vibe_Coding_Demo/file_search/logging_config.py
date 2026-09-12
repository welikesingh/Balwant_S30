"""Logging configuration for the file search application."""

import logging
from datetime import datetime
from pathlib import Path


LOGGER_NAME = "file_search"


def setup_logging(root: Path) -> Path:
    """Configure console and per-run file logging, returning the log path."""
    log_folder = Path(root) / "logs"
    log_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_path = log_folder / f"file_search_{timestamp}.log"

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Avoid duplicate messages if main() is called more than once in a process.
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return log_path
