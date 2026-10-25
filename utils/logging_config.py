"""Logging configuration for CyberScope.

Provides a centralized logger setup used across the application.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "cyberscope.log"

DEFAULT_LEVEL = logging.INFO

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = DEFAULT_LEVEL,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """Configure the root logger and return the CyberScope logger.

    Parameters
    ----------
    level : int
        Logging level (default INFO).
    log_to_file : bool
        Write logs to ``logs/cyberscope.log`` with rotation.
    log_to_console : bool
        Emit logs to stdout.

    Returns
    -------
    logging.Logger
        The ``cyberscope`` logger instance.
    """

    logger = logging.getLogger("cyberscope")
    logger.setLevel(level)
    logger.propagate = False

    # Avoid duplicate handlers if called multiple times.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(_FORMAT, datefmt=_DATEFMT)

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_to_file:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as exc:
            # Fall back to console-only logging if the log file is not
            # writable (e.g. created by a previous root-owned run).
            logger.warning("Could not open log file %s: %s", LOG_FILE, exc)

    logger.debug("Logging initialized (level=%s)", logging.getLevelName(level))
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger for the given module name."""
    return logging.getLogger("cyberscope").getChild(name)
