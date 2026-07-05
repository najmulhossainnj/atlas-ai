"""Event models for the message bus."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import uuid


class EventType(str, Enum):
    """Types of events in the system."""
    AGENT_CREATED = "agent.created"
    AGENT_DELETED = "agent.deleted"
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_ERROR = "agent.error"
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    TOOL_CALLED = "tool.called"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_CONSOLIDATED = "memory.consolidated"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    ERROR = "error"
    CUSTOM = "custom"


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    """Base event class."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM
    source: str = ""
    target: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "source": self.source,
            "target": self.target,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            event_type=EventType(data.get("event_type", EventType.CUSTOM)),
            source=data.get("source", ""),
            target=data.get("target"),
            data=data.get("data", {}),
            priority=EventPriority(data.get("priority", EventPriority.NORMAL)),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            correlation_id=data.get("correlation_id"),
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class EventMessage:
    """A message wrapper for events in the queue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: Optional[Event] = None
    raw_data: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_json(self) -> str:
        data = {
            "id": self.id,
            "event": self.event.to_dict() if self.event else None,
            "raw_data": self.raw_data,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> EventMessage:
        data = json.loads(json_str)
        event = Event.from_dict(data["event"]) if data.get("event") else None
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            event=event,
            raw_data=data.get("raw_data"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
        )


@dataclass
class Subscription:
    """Subscription to specific event types."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    event_types: list[EventType] = field(default_factory=list)
    callback: Optional[Callable] = None
    filter_fn: Optional[Callable[[Event], bool]] = None
    async_callback: Optional[Callable[[Event], Any]] = None
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def matches(self, event: Event) -> bool:
        if not self.enabled:
            return False
        if not any(event.event_type == et for et in self.event_types):
            return False
        if self.filter_fn and not self.filter_fn(event):
            return False
        return True

    async def notify(self, event: Event) -> None:
        if self.async_callback:
            await self.async_callback(event)
        elif self.callback:
            self.callback(event)
