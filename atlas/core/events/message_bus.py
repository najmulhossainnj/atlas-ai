"""Redis-based message bus for async agent communication."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Optional
import uuid

from atlas.core.events.models import (
    Event,
    EventMessage,
    EventPriority,
    EventType,
    Subscription,
)
from atlas.core.events.subscribers import SubscriberManager

logger = logging.getLogger(__name__)


class MessageBus:
    """Redis-based pub/sub message bus with in-memory fallback."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        channel_prefix: str = "atlas:events",
        enable_redis: bool = True,
        enable_persistence: bool = True,
    ):
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.enable_redis = enable_redis
        self.enable_persistence = enable_persistence
        self._redis = None
        self._redis_pubsub = None
        self._in_memory_subscribers: dict[str, list[Subscription]] = {}
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._subscriber_manager = SubscriberManager()
        self._locks: dict[str, asyncio.Lock] = {}

    async def connect(self) -> None:
        """Connect to Redis if configured."""
        if not self.enable_redis or not self.redis_url:
            logger.info("Message bus running in in-memory mode")
            return

        try:
            import redis.asyncio as redis
            
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info("Connected to Redis message bus")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory mode: {e}")
            self.enable_redis = False
            self._redis = None

    async def disconnect(self) -> None:
        """Disconnect from Redis and cleanup."""
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.close()
            self._redis = None

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        """Async context manager for lifecycle management."""
        await self.connect()
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        
        try:
            yield
        finally:
            await self.disconnect()

    async def start(self) -> None:
        """Start the message bus."""
        if self._running:
            return
        await self.connect()
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())

    async def stop(self) -> None:
        """Stop the message bus."""
        await self.disconnect()

    async def publish(self, event: Event) -> int:
        """Publish an event to the message bus."""
        event.correlation_id = event.correlation_id or str(uuid.uuid4())
        
        await self._log_event("publish", event)

        if self.enable_redis and self._redis:
            return await self._publish_redis(event)
        else:
            return await self._publish_in_memory(event)

    async def _publish_redis(self, event: Event) -> int:
        """Publish event to Redis."""
        channel = f"{self.channel_prefix}:{event.event_type.value}"
        message = EventMessage(event=event).to_json()
        
        subscribers = await self._redis.publish(channel, message)
        
        await self._persist_event(event)
        
        return subscribers

    async def _publish_in_memory(self, event: Event) -> int:
        """Publish event in-memory."""
        channel = event.event_type.value
        subscribers = 0
        
        if channel in self._in_memory_subscribers:
            for sub in self._in_memory_subscribers[channel]:
                if sub.matches(event):
                    await sub.notify(event)
                    subscribers += 1
        
        wildcard_channel = "*"
        if wildcard_channel in self._in_memory_subscribers:
            for sub in self._in_memory_subscribers[wildcard_channel]:
                if sub.matches(event):
                    await sub.notify(event)
                    subscribers += 1
        
        await self._event_queue.put(event)
        
        return subscribers

    async def subscribe(
        self,
        event_types: list[EventType],
        callback: Callable[[Event], Any],
        name: Optional[str] = None,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> Subscription:
        """Subscribe to specific event types."""
        subscription = Subscription(
            name=name or str(uuid.uuid4()),
            event_types=event_types,
            async_callback=callback if asyncio.iscoroutinefunction(callback) else None,
            callback=callback if not asyncio.iscoroutinefunction(callback) else None,
            filter_fn=filter_fn,
        )

        for event_type in event_types:
            channel = event_type.value
            if channel not in self._in_memory_subscribers:
                self._in_memory_subscribers[channel] = []
            self._in_memory_subscribers[channel].append(subscription)

        await self._subscriber_manager.register(subscription)
        
        return subscription

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        removed = await self._subscriber_manager.unregister(subscription_id)
        
        for channel_subs in self._in_memory_subscribers.values():
            channel_subs[:] = [s for s in channel_subs if s.id != subscription_id]
        
        return removed

    async def request(
        self,
        target: str,
        event_type: EventType,
        data: dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Event]:
        """Send a request and wait for response."""
        correlation_id = str(uuid.uuid4())
        response_event = asyncio.Event()
        response_data: dict[str, Any] = {}

        async def response_handler(event: Event) -> None:
            if event.correlation_id == correlation_id:
                response_data["event"] = event
                response_event.set()

        subscription = await self.subscribe(
            [EventType(f"{target}.response")],
            response_handler,
            name=f"response_handler_{correlation_id}",
        )

        try:
            await self.publish(Event(
                event_type=event_type,
                source="request",
                target=target,
                data=data,
                correlation_id=correlation_id,
            ))

            try:
                await asyncio.wait_for(response_event.wait(), timeout=timeout)
                return response_data.get("event")
            except asyncio.TimeoutError:
                return None
        finally:
            await self.unsubscribe(subscription.id)

    async def broadcast(self, event: Event) -> int:
        """Broadcast to all subscribers regardless of type."""
        event.event_type = EventType.CUSTOM
        
        await self._log_event("broadcast", event)
        
        subscribers = 0
        for channel_subs in self._in_memory_subscribers.values():
            for sub in channel_subs:
                if sub.enabled and (not sub.filter_fn or sub.filter_fn(event)):
                    await sub.notify(event)
                    subscribers += 1
        
        if self.enable_redis and self._redis:
            channel = f"{self.channel_prefix}:broadcast"
            message = EventMessage(event=event).to_json()
            await self._redis.publish(channel, message)
        
        return subscribers

    async def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get historical events from persistence."""
        if not self.enable_persistence:
            return []
        
        events = []
        
        if self.enable_redis and self._redis:
            events = await self._get_events_redis(event_type, limit)
        
        return events[-limit:]

    async def _persist_event(self, event: Event) -> None:
        """Persist event to storage."""
        if not self.enable_persistence:
            return
        
        if self.enable_redis and self._redis:
            try:
                key = f"{self.channel_prefix}:history:{event.event_type.value}"
                await self._redis.lpush(key, EventMessage(event=event).to_json())
                await self._redis.ltrim(key, 0, 999)
            except Exception as e:
                logger.error(f"Failed to persist event: {e}")

    async def _get_events_redis(
        self,
        event_type: Optional[EventType],
        limit: int,
    ) -> list[Event]:
        """Get events from Redis."""
        events = []
        
        try:
            if event_type:
                keys = [f"{self.channel_prefix}:history:{event_type.value}"]
            else:
                keys = await self._redis.keys(f"{self.channel_prefix}:history:*")
            
            for key in keys[:10]:
                messages = await self._redis.lrange(key, 0, limit - 1)
                for msg in messages:
                    try:
                        event_msg = EventMessage.from_json(msg)
                        if event_msg.event:
                            events.append(event_msg.event)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to get events from Redis: {e}")
        
        return events

    async def _process_events(self) -> None:
        """Background task to process queued events."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )
                
                await self._log_event("process", event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _log_event(self, action: str, event: Event) -> None:
        """Log event for debugging."""
        logger.debug(
            f"Event {action}: type={event.event_type.value}, "
            f"source={event.source}, target={event.target}, "
            f"correlation_id={event.correlation_id}"
        )

    def get_stats(self) -> dict[str, Any]:
        """Get message bus statistics."""
        total_subscribers = sum(
            len(subs) for subs in self._in_memory_subscribers.values()
        )
        
        return {
            "redis_enabled": self.enable_redis and self._redis is not None,
            "redis_url": self.redis_url,
            "running": self._running,
            "queue_size": self._event_queue.qsize(),
            "total_subscribers": total_subscribers,
            "channels": list(self._in_memory_subscribers.keys()),
        }


_global_message_bus: Optional[MessageBus] = None


async def get_message_bus() -> MessageBus:
    """Get the global message bus instance."""
    global _global_message_bus
    if _global_message_bus is None:
        _global_message_bus = MessageBus()
        await _global_message_bus.start()
    return _global_message_bus


async def shutdown_message_bus() -> None:
    """Shutdown the global message bus."""
    global _global_message_bus
    if _global_message_bus:
        await _global_message_bus.stop()
        _global_message_bus = None
