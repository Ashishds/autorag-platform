"""Structured logging setup (LLD §16 — trace_id-aware JSON logs)."""

import logging

import structlog

from app.config import settings


def configure_logging() -> None:
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        cache_logger_on_first_use=True,
    )


log = structlog.get_logger("autorag")
