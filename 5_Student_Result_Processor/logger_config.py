import logging
import os

LOG_FOLDER = "logs"
LOG_FILE = os.path.join(LOG_FOLDER, "student_system.log")


def setup_logger():
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)

    logger = logging.getLogger("student_system")
    logger.setLevel(logging.ERROR)

    # avoid adding the same handler again if this is called twice
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    return logger
