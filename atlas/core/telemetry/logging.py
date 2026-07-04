"""Structured logging setup for Atlas."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from typing import Any, Optional
import structlog

from atlas.core.telemetry.tracer import get_tracer


def setup_logging(
    level: str = "INFO",
    json_logs: bool = True,
    service_name: str = "atlas",
) -> None:
    """Configure structured logging for Atlas."""
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class AtlasLogger:
    """Enhanced logger with structured output and tracing."""

    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
        self.name = name

    def _add_trace_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Add tracing context to log entries."""
        try:
            tracer = get_tracer()
            current_span = tracer.current_span
            if current_span:
                kwargs["trace_id"] = current_span.trace_id
                kwargs["span_id"] = current_span.span_id
        except Exception:
            pass
        return kwargs

    def debug(self, msg: str, **kwargs: Any) -> None:
        self.logger.debug(msg, **self._add_trace_context(kwargs))

    def info(self, msg: str, **kwargs: Any) -> None:
        self.logger.info(msg, **self._add_trace_context(kwargs))

    def warning(self, msg: str, **kwargs: Any) -> None:
        self.logger.warning(msg, **self._add_trace_context(kwargs))

    def error(self, msg: str, **kwargs: Any) -> None:
        self.logger.error(msg, **self._add_trace_context(kwargs))

    def critical(self, msg: str, **kwargs: Any) -> None:
        self.logger.critical(msg, **self._add_trace_context(kwargs))

    def exception(self, msg: str, **kwargs: Any) -> None:
        self.logger.exception(msg, **self._add_trace_context(kwargs))

    def log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Log an structured event."""
        self.logger.info(
            f"event: {event_type}",
            event_type=event_type,
            **data,
        )


def get_logger(name: str = "atlas") -> AtlasLogger:
    """Get a structured logger."""
    return AtlasLogger(name)


class LogCapture:
    """Capture logs for testing."""

    def __init__(self):
        self.records: list[dict[str, Any]] = []
        self._handler: Optional[logging.Handler] = None

    def start(self) -> None:
        """Start capturing logs."""
        self._handler = LogHandler(self.records)
        logging.root.addHandler(self._handler)

    def stop(self) -> None:
        """Stop capturing logs."""
        if self._handler:
            logging.root.removeHandler(self._handler)
            self._handler = None
        self.records.clear()

    def get_records(self) -> list[dict[str, Any]]:
        """Get captured records."""
        return self.records.copy()

    def clear(self) -> None:
        """Clear captured records."""
        self.records.clear()


class LogHandler(logging.Handler):
    """Handler to capture log records."""

    def __init__(self, records: list):
        super().__init__()
        self.records = records

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append({
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        })
