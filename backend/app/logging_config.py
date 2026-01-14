"""
Structured logging configuration using structlog.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log events."""
    event_dict["app"] = "poker-helper"
    return event_dict


def setup_logging(debug: bool = False) -> None:
    """
    Configure structlog for the application.
    
    Args:
        debug: If True, use development-friendly output; otherwise JSON.
    """
    # Shared processors for both structlog and stdlib
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if debug:
        # Development: colored console output
        processors: list[Processor] = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if debug else logging.INFO,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        A bound structlog logger
    """
    return structlog.get_logger(name)


# Convenience function for logging CV events
def log_cv_detection(
    logger: structlog.BoundLogger,
    detection_type: str,
    results: dict[str, Any],
    processing_time_ms: float,
) -> None:
    """Log a computer vision detection event."""
    logger.info(
        "cv_detection",
        detection_type=detection_type,
        results=results,
        processing_time_ms=round(processing_time_ms, 2),
    )


def log_recommendation(
    logger: structlog.BoundLogger,
    hand: str,
    position: str,
    stack_bb: float,
    action: str,
    reason: str,
) -> None:
    """Log a GTO recommendation event."""
    logger.info(
        "gto_recommendation",
        hand=hand,
        position=position,
        stack_bb=round(stack_bb, 1),
        action=action,
        reason=reason,
    )


def log_api_request(
    logger: structlog.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Log an API request."""
    log_level = "warning" if status_code >= 400 else "info"
    getattr(logger, log_level)(
        "api_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
    )
