"""
Structured JSON logging setup.

Configures Python's logging to output structured JSON lines,
suitable for log aggregation tools (ELK, CloudWatch, etc.).
"""

import logging
import sys

from pythonjsonlogger import jsonlogger

from store_intel.config import settings


def setup_logging() -> logging.Logger:
    """
    Configure and return the application-wide logger.

    Call this once at application startup (in main.py).
    All other modules should use: `logger = logging.getLogger("store_intel")`
    """
    logger = logging.getLogger("store_intel")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Avoid duplicate handlers on reload
    if logger.handlers:
        return logger

    # ── JSON handler → stdout ───────────────────────────────
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info(
        "Logging initialized",
        extra={"log_level": settings.log_level, "environment": settings.environment},
    )

    return logger
