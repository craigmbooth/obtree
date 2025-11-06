"""Logging configuration using structlog."""
import logging
import sys
import structlog
from structlog.types import FilteringBoundLogger

from app.config import settings


def configure_logging() -> None:
    """Configure structlog for the application."""

    # Determine log level based on DEBUG setting
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level to event dict
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add context from thread-local storage
            structlog.contextvars.merge_contextvars,
            # Format stack traces
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Render as JSON in production, console in development
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)
