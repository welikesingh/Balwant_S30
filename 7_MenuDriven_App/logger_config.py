import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

def create_file_handler(file_name, level, formatter):
    """Create a configured file handler."""
    handler = logging.FileHandler(file_name, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler

def setup_logging():
    """Configure application, error, and console logging."""
    log_folder = Path(__file__).parent / "logs"
    log_folder.mkdir(exist_ok=True)
    logger = logging.getLogger("application")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger
    formatter = logging.Formatter(LOG_FORMAT)
    application_file = create_file_handler(log_folder / "application.log", logging.DEBUG, formatter)
    error_file = create_file_handler(log_folder / "error.log", logging.ERROR, formatter)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    logger.addHandler(application_file)
    logger.addHandler(error_file)
    logger.addHandler(console)
    return logger
