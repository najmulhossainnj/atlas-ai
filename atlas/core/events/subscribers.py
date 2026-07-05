"""Subscriber management for the message bus."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import uuid

from atlas.core.events.models import Event, EventType, Subscription


@dataclass
class Subscriber:
    """A subscriber to events."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    event_types: list[EventType] = field(default_factory=list)
    callback: Optional[Callable] = None
    async_callback: Optional[Callable] = None
    filter_fn: Optional[Callable[[Event], bool]] = None
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class SubscriberManager:
    """Manages event subscriptions."""

    def __init__(self):
        self._subscriptions: dict[str, Subscription] = {}
        self._by_event_type: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def register(self, subscription: Subscription) -> None:
        """Register a new subscription."""
        async with self._lock:
            self._subscriptions[subscription.id] = subscription
            
            for event_type in subscription.event_types:
                type_key = event_type.value
                if type_key not in self._by_event_type:
                    self._by_event_type[type_key] = set()
                self._by_event_type[type_key].add(subscription.id)

    async def unregister(self, subscription_id: str) -> bool:
        """Unregister a subscription."""
        async with self._lock:
            subscription = self._subscriptions.pop(subscription_id, None)
            if not subscription:
                return False
            
            for event_type in subscription.event_types:
                type_key = event_type.value
                if type_key in self._by_event_type:
                    self._by_event_type[type_key].discard(subscription_id)
            
            return True

    async def get(self, subscription_id: str) -> Optional[Subscription]:
        """Get a subscription by ID."""
        async with self._lock:
            return self._subscriptions.get(subscription_id)

    async def get_for_event_type(self, event_type: EventType) -> list[Subscription]:
        """Get all subscriptions for an event type."""
        async with self._lock:
            type_key = event_type.value
            sub_ids = self._by_event_type.get(type_key, set())
            return [
                self._subscriptions[sid]
                for sid in sub_ids
                if sid in self._subscriptions and self._subscriptions[sid].enabled
            ]

    async def get_all(self) -> list[Subscription]:
        """Get all subscriptions."""
        async with self._lock:
            return list(self._subscriptions.values())

    async def enable(self, subscription_id: str) -> bool:
        """Enable a subscription."""
        async with self._lock:
            subscription = self._subscriptions.get(subscription_id)
            if subscription:
                subscription.enabled = True
                return True
            return False

    async def disable(self, subscription_id: str) -> bool:
        """Disable a subscription."""
        async with self._lock:
            subscription = self._subscriptions.get(subscription_id)
            if subscription:
                subscription.enabled = False
                return True
            return False

    async def count(self) -> int:
        """Count total subscriptions."""
        async with self._lock:
            return len(self._subscriptions)

    async def count_by_event_type(self, event_type: EventType) -> int:
        """Count subscriptions for an event type."""
        async with self._lock:
            type_key = event_type.value
            return len(self._by_event_type.get(type_key, set()))

    async def clear(self) -> None:
        """Clear all subscriptions."""
        async with self._lock:
            self._subscriptions.clear()
            self._by_event_type.clear()
