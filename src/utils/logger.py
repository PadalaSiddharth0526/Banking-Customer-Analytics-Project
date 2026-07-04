"""Centralized logger configuration for the banking analytics project."""

import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "reports" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that writes to console and a shared log file.

    Args:
        name: Usually __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers on repeated imports

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOG_DIR / "pipeline.log")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
