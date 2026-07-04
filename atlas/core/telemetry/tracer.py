"""OpenTelemetry tracer integration."""

from __future__ import annotations

import asyncio
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional
import logging

logger = logging.getLogger(__name__)


class SpanKind(str, Enum):
    """Kinds of spans."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span status codes."""
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class Span:
    """A tracing span."""
    name: str
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    kind: SpanKind = SpanKind.INTERNAL
    status: SpanStatus = SpanStatus.UNSET
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[dict[str, Any]] = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def set_status(self, status: SpanStatus, message: Optional[str] = None) -> None:
        self.status = status
        if message:
            self.attributes["status.message"] = message

    def record_exception(self, exception: Exception) -> None:
        self.events.append({
            "name": "exception",
            "timestamp": time.time(),
            "attributes": {
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
                "exception.stacktrace": str(exception),
            },
        })
        self.status = SpanStatus.ERROR

    def end(self) -> None:
        if self.end_time is None:
            self.end_time = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": (self.end_time - self.start_time) * 1000 if self.end_time else None,
            "attributes": self.attributes,
            "events": self.events,
            "links": self.links,
        }


_tracer_state: ContextVar[Optional[Span]] = ContextVar("tracer_state", default=None)


class Tracer:
    """Distributed tracing with OpenTelemetry-compatible interface."""

    def __init__(
        self,
        service_name: str = "atlas",
        exporter: Optional[Any] = None,
        enable_logging: bool = True,
    ):
        self.service_name = service_name
        self.exporter = exporter
        self.enable_logging = enable_logging
        self._spans: list[Span] = []
        self._lock = asyncio.Lock()
        self._enabled = True

    @property
    def current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return _tracer_state.get()

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span: Optional[Span] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Span:
        """Start a new span."""
        parent = parent_span or self.current_span
        
        span = Span(
            name=name,
            kind=kind,
            parent_span_id=parent.span_id if parent else None,
            attributes=attributes or {},
        )
        
        span.set_attribute("service.name", self.service_name)
        span.set_attribute("span.kind", kind.value)
        
        return span

    async def start_span_async(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span: Optional[Span] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Span:
        """Start a new span asynchronously."""
        span = self.start_span(name, kind, parent_span, attributes)
        await self.record_span(span)
        return span

    async def record_span(self, span: Span) -> None:
        """Record a completed span."""
        async with self._lock:
            self._spans.append(span)
            
            if len(self._spans) > 10000:
                self._spans = self._spans[-5000:]

        if self.enable_logging:
            logger.debug(
                f"Span recorded: {span.name}",
                extra={
                    "trace_id": span.trace_id,
                    "span_id": span.span_id,
                    "duration_ms": (span.end_time - span.start_time) * 1000 if span.end_time else None,
                },
            )

        if self.exporter:
            await self._export_span(span)

    async def _export_span(self, span: Span) -> None:
        """Export a span to the configured exporter."""
        try:
            if hasattr(self.exporter, "export"):
                await self.exporter.export([span])
            elif hasattr(self.exporter, "__call__"):
                self.exporter(span)
        except Exception as e:
            logger.error(f"Failed to export span: {e}")

    async def get_traces(
        self,
        trace_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Span]:
        """Get recorded spans."""
        async with self._lock:
            spans = self._spans.copy()
        
        if trace_id:
            spans = [s for s in spans if s.trace_id == trace_id]
        
        return spans[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get tracer statistics."""
        return {
            "service_name": self.service_name,
            "spans_recorded": len(self._spans),
            "enabled": self._enabled,
            "has_exporter": self.exporter is not None,
        }

    def disable(self) -> None:
        """Disable tracing."""
        self._enabled = False

    def enable(self) -> None:
        """Enable tracing."""
        self._enabled = True


class SpanContext:
    """Context manager for spans."""

    def __init__(
        self,
        tracer: Tracer,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[dict[str, Any]] = None,
    ):
        self.tracer = tracer
        self.name = name
        self.kind = kind
        self.attributes = attributes
        self.span: Optional[Span] = None
        self._token = None

    async def __aenter__(self) -> Span:
        self.span = await self.tracer.start_span_async(
            self.name,
            self.kind,
            attributes=self.attributes,
        )
        self._token = _tracer_state.set(self.span)
        return self.span

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.span:
            if exc_type:
                self.span.record_exception(exc_val)
            self.span.end()
            await self.tracer.record_span(self.span)
        
        if self._token:
            _tracer_state.reset(self._token)


_global_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "atlas") -> Tracer:
    """Get the global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name=service_name)
    return _global_tracer


async def trace(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[dict[str, Any]] = None,
) -> AsyncIterator[Span]:
    """Decorator/async context manager for tracing."""
    tracer = get_tracer()
    async with SpanContext(tracer, name, kind, attributes) as span:
        yield span
