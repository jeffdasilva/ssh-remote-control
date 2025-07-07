"""Logging configuration for SSH Remote Control."""

from __future__ import annotations

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# mypy: disable-error-code=misc


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """Set up logging configuration with file and console handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files (relative to project root)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Generate log filename with timestamp
    now = datetime.now()  # type: ignore[misc]
    timestamp = now.strftime("%Y%m%d_%H%M%S")  # type: ignore[misc]
    log_file_path = (  # type: ignore[misc]
        log_path / f"ssh-remote-control_{timestamp}.log"
    )

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(fmt="%(levelname)s - %(message)s")

    # Get root logger
    root_logger = logging.getLogger()

    # Convert log level string to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    numeric_level = level_map.get(log_level.upper(), logging.INFO)  # type: ignore[misc]
    root_logger.setLevel(numeric_level)  # type: ignore[misc]

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file_path),  # type: ignore[misc]
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)  # type: ignore[misc]
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)  # type: ignore[misc]
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)  # type: ignore[misc]
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)  # type: ignore[misc]
    logging.getLogger("asyncio").setLevel(logging.WARNING)  # type: ignore[misc]

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(  # type: ignore[misc]
        "Logging configured - File: %s, Level: %s",
        str(log_file_path),
        log_level,  # type: ignore[misc]
    )
