"""
CRM VITAO360 — Structured Logging Configuration

JSON logging in production, human-readable in development.
Import and call setup_logging() in main.py before app creation.
"""

from __future__ import annotations

import json
import logging
import os
import sys


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects for production use.
    Compatible with log aggregators (Railway, Datadog, Papertrail, etc.).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_obj["stack_info"] = self.formatStack(record.stack_info)
        # Include any extra fields passed via extra={...}
        _standard_keys = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for key, val in record.__dict__.items():
            if key not in _standard_keys and not key.startswith("_"):
                log_obj[key] = val
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(level: str | None = None) -> None:
    """
    Configure root logger.

    - Production (ENV=production or RAILWAY_ENVIRONMENT set): JSON formatter.
    - Development (default): standard human-readable format with colors via
      uvicorn's default handler; we only set the level here.

    Call once at startup, before FastAPI app creation.
    """
    env = os.getenv("ENV", os.getenv("RAILWAY_ENVIRONMENT", "development")).lower()
    is_production = env in ("production", "prod", "railway")

    log_level_name = level or os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate output
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if is_production:
        handler.setFormatter(JSONFormatter())
    else:
        # Development: simple readable format
        fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
        handler.setFormatter(logging.Formatter(fmt, datefmt="%H:%M:%S"))

    root_logger.addHandler(handler)

    # Quieter third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug(
        "Logging configured | env=%s level=%s json=%s",
        env, log_level_name, is_production,
    )
