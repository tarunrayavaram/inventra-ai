"""Logging configuration."""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        from config.settings import get_settings
        settings = get_settings()

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper()))

    return logger
