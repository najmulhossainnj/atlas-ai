"""Worker implementation for task queue."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    """Configuration for a worker."""
    worker_id: str
    queue_size: int = 10
    timeout: float = 60.0
    max_retries: int = 3
    poll_interval: float = 1.0


class Worker:
    """Worker that processes tasks from a queue."""

    def __init__(self, config: WorkerConfig, queue: Any):
        self.config = config
        self.queue = queue
        self._running = False
        self._tasks_processed = 0
        self._tasks_failed = 0

    async def start(self) -> None:
        """Start the worker."""
        self._running = True
        logger.info(f"Worker {self.config.worker_id} started")
        
        while self._running:
            try:
                task = await self.queue.dequeue(timeout=self.config.poll_interval)
                if task:
                    await self._process(task)
                    self._tasks_processed += 1
            except Exception as e:
                logger.error(f"Worker error: {e}")
                self._tasks_failed += 1

    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        logger.info(f"Worker {self.config.worker_id} stopped")

    async def _process(self, task: Any) -> None:
        """Process a single task."""
        logger.debug(f"Processing task: {task.name}")
        
    def get_stats(self) -> dict[str, Any]:
        return {
            "worker_id": self.config.worker_id,
            "running": self._running,
            "tasks_processed": self._tasks_processed,
            "tasks_failed": self._tasks_failed,
        }


class WorkerPool:
    """Pool of workers."""

    def __init__(self, size: int = 4):
        self.size = size
        self.workers: list[Worker] = []
        self._running = False

    async def start(self, queue: Any) -> None:
        """Start all workers in the pool."""
        self._running = True
        
        for i in range(self.size):
            config = WorkerConfig(worker_id=f"worker-{i}")
            worker = Worker(config, queue)
            self.workers.append(worker)
        
        tasks = [asyncio.create_task(w.start()) for w in self.workers]
        await asyncio.gather(*tasks)

    async def stop(self) -> None:
        """Stop all workers."""
        self._running = False
        for worker in self.workers:
            await worker.stop()
