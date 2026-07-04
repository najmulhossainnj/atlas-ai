"""Async task queue using Redis."""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A task in the queue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    function: str = ""
    args: tuple = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 60.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "function": self.function,
            "args": self.args,
            "kwargs": self.kwargs,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            function=data.get("function", ""),
            args=tuple(data.get("args", [])),
            kwargs=data.get("kwargs", {}),
            status=TaskStatus(data.get("status", TaskStatus.PENDING)),
            result=data.get("result"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 60.0),
            metadata=data.get("metadata", {}),
        )


class TaskQueue:
    """Redis-based async task queue."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        queue_name: str = "atlas:tasks",
        enable_redis: bool = True,
    ):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.enable_redis = enable_redis
        self._redis = None
        self._handlers: dict[str, Callable] = {}
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect to Redis."""
        if not self.enable_redis:
            return
        
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                self.redis_url or "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory queue: {e}")
            self.enable_redis = False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def register_handler(self, function_name: str, handler: Callable) -> None:
        """Register a task handler."""
        self._handlers[function_name] = handler

    async def enqueue(
        self,
        function: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Add a task to the queue."""
        task = Task(
            name=function,
            function=function,
            args=args,
            kwargs=kwargs,
        )
        
        if self.enable_redis and self._redis:
            await self._redis.lpush(self.queue_name, json.dumps(task.to_dict()))
        else:
            await self._enqueue_in_memory(task)
        
        return task.id

    async def _enqueue_in_memory(self, task: Task) -> None:
        """Enqueue task in memory."""
        from collections import deque
        if not hasattr(self, "_in_memory_queue"):
            self._in_memory_queue: asyncio.Queue[Task] = asyncio.Queue()
        await self._in_memory_queue.put(task)

    async def dequeue(self, timeout: float = 5.0) -> Optional[Task]:
        """Get a task from the queue."""
        if self.enable_redis and self._redis:
            result = await self._redis.brpop(self.queue_name, timeout=timeout)
            if result:
                _, data = result
                return Task.from_dict(json.loads(data))
        else:
            try:
                return await asyncio.wait_for(
                    self._in_memory_queue.get(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass
        return None

    async def start_worker(self, worker_id: str = "worker-1") -> None:
        """Start a worker to process tasks."""
        async with self._lock:
            self._running = True
        
        logger.info(f"Starting worker {worker_id}")
        
        while self._running:
            task = await self.dequeue()
            if task:
                await self._process_task(task)
            
            await asyncio.sleep(0.1)

    async def _process_task(self, task: Task) -> None:
        """Process a single task."""
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.utcnow()
        
        try:
            handler = self._handlers.get(task.function)
            if not handler:
                raise ValueError(f"No handler registered for function: {task.function}")
            
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(
                    handler(*task.args, **task.kwargs),
                    timeout=task.timeout,
                )
            else:
                result = handler(*task.args, **task.kwargs)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                await self.enqueue(task.function, *task.args, **task.kwargs)
            else:
                task.status = TaskStatus.FAILED
        
        finally:
            task.completed_at = datetime.utcnow()

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task."""
        if self.enable_redis and self._redis:
            keys = await self._redis.keys(f"{self.queue_name}:{task_id}:*")
            if keys:
                data = await self._redis.get(keys[0])
                if data:
                    return Task.from_dict(json.loads(data)).status
        return None

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        return False

    async def stop(self) -> None:
        """Stop the worker."""
        async with self._lock:
            self._running = False
        
        for task in self._worker_tasks:
            task.cancel()
        
        await self.disconnect()


async def example_task(x: int, y: int) -> int:
    """Example task for testing."""
    await asyncio.sleep(0.1)
    return x + y
