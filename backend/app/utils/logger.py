"""
Structured logger for the application.
"""
import logging
import sys
from typing import Any

# Default format for development
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger


def log_extra(logger: logging.Logger, msg: str, level: int = logging.INFO, **extra: Any) -> None:
    """Log a message with optional extra key-value fields."""
    logger.log(level, msg, extra=extra)
