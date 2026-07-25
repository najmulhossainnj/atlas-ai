"""Task queue module using Redis."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable

import redis.asyncio as redis

from atlas.core.config import get_settings


class JobStatus(str, Enum):
    """Job status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Represents a queued job."""
    
    def __init__(
        self,
        id: str | None = None,
        name: str = "",
        payload: dict[str, Any] | None = None,
        status: JobStatus = JobStatus.PENDING,
        result: Any | None = None,
        error: str | None = None,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        retries: int = 0,
        max_retries: int = 3,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.payload = payload or {}
        self.status = status
        self.result = result
        self.error = error
        self.created_at = created_at or datetime.utcnow()
        self.started_at = started_at
        self.completed_at = completed_at
        self.retries = retries
        self.max_retries = max_retries
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "max_retries": self.max_retries,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        """Create from dictionary."""
        status = data.get("status", JobStatus.PENDING)
        if isinstance(status, str):
            status = JobStatus(status)
        
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            payload=data.get("payload", {}),
            status=status,
            result=data.get("result"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            retries=data.get("retries", 0),
            max_retries=data.get("max_retries", 3),
        )


class Queue:
    """Redis-based task queue."""
    
    def __init__(
        self,
        name: str = "default",
        default_timeout: int = 300,
    ):
        """Initialize queue.
        
        Args:
            name: Queue name
            default_timeout: Default job timeout in seconds
        """
        self.name = name
        self.default_timeout = default_timeout
        self._client: redis.Redis | None = None
        self._processing_set = f"queue:{name}:processing"
        self._jobs_hash = f"queue:{name}:jobs"
        self._result_prefix = f"queue:{name}:result"
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            settings = get_settings()
            self._client = redis.from_url(
                settings.redis.url,
                db=settings.redis.db,
                password=settings.redis.password,
                max_connections=settings.redis.max_connections,
                decode_responses=True,
            )
        return self._client
    
    async def enqueue(
        self,
        name: str,
        payload: dict[str, Any],
        delay: int = 0,
        max_retries: int = 3,
    ) -> Job:
        """Enqueue a job.
        
        Args:
            name: Job name
            payload: Job payload
            delay: Delay in seconds before job runs
            max_retries: Maximum retry attempts
            
        Returns:
            Created job
        """
        job = Job(
            name=name,
            payload=payload,
            max_retries=max_retries,
        )
        
        client = await self.get_client()
        queue_key = f"queue:{self.name}:{delay}" if delay > 0 else f"queue:{self.name}"
        
        # Store job data
        await client.hset(self._jobs_hash, job.id, json.dumps(job.to_dict()))
        
        # Add to queue
        await client.rpush(queue_key, job.id)
        
        return job
    
    async def dequeue(self, timeout: int = 5) -> Job | None:
        """Dequeue a job.
        
        Args:
            timeout: Blocking timeout in seconds
            
        Returns:
            Job or None if queue is empty
        """
        client = await self.get_client()
        
        # Try to get from immediate queue first
        result = await client.blpop(
            f"queue:{self.name}",
            timeout=timeout,
        )
        
        if result is None:
            return None
        
        _, job_id = result
        job_data = await client.hget(self._jobs_hash, job_id)
        
        if job_data is None:
            return None
        
        job = Job.from_dict(json.loads(job_data))
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        # Move to processing set
        await client.sadd(self._processing_set, job_id)
        await client.hset(self._jobs_hash, job_id, json.dumps(job.to_dict()))
        
        return job
    
    async def complete(self, job_id: str, result: Any) -> None:
        """Mark job as completed.
        
        Args:
            job_id: Job ID
            result: Job result
        """
        client = await self.get_client()
        
        job_data = await client.hget(self._jobs_hash, job_id)
        if job_data:
            job = Job.from_dict(json.loads(job_data))
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.utcnow()
            
            await client.hset(self._jobs_hash, job_id, json.dumps(job.to_dict()))
            await client.srem(self._processing_set, job_id)
            
            # Store result with TTL
            await client.setex(
                f"{self._result_prefix}:{job_id}",
                3600,
                json.dumps(result),
            )
    
    async def fail(self, job_id: str, error: str) -> None:
        """Mark job as failed.
        
        Args:
            job_id: Job ID
            error: Error message
        """
        client = await self.get_client()
        
        job_data = await client.hget(self._jobs_hash, job_id)
        if job_data:
            job = Job.from_dict(json.loads(job_data))
            job.error = error
            
            if job.retries < job.max_retries:
                # Retry the job
                job.retries += 1
                job.status = JobStatus.PENDING
                await client.rpush(f"queue:{self.name}", job_id)
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
            
            await client.hset(self._jobs_hash, job_id, json.dumps(job.to_dict()))
            await client.srem(self._processing_set, job_id)
    
    async def cancel(self, job_id: str) -> bool:
        """Cancel a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if cancelled
        """
        client = await self.get_client()
        
        job_data = await client.hget(self._jobs_hash, job_id)
        if job_data:
            job = Job.from_dict(json.loads(job_data))
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            
            await client.hset(self._jobs_hash, job_id, json.dumps(job.to_dict()))
            await client.srem(self._processing_set, job_id)
            
            return True
        
        return False
    
    async def get_job(self, job_id: str) -> Job | None:
        """Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job or None
        """
        client = await self.get_client()
        
        job_data = await client.hget(self._jobs_hash, job_id)
        if job_data:
            return Job.from_dict(json.loads(job_data))
        
        return None
    
    async def get_result(self, job_id: str) -> Any | None:
        """Get job result.
        
        Args:
            job_id: Job ID
            
        Returns:
            Result or None
        """
        client = await self.get_client()
        
        result = await client.get(f"{self._result_prefix}:{job_id}")
        if result:
            return json.loads(result)
        
        return None
    
    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 100,
    ) -> list[Job]:
        """List jobs.
        
        Args:
            status: Filter by status
            limit: Maximum jobs to return
            
        Returns:
            List of jobs
        """
        client = await self.get_client()
        
        all_jobs = await client.hgetall(self._jobs_hash)
        jobs = []
        
        for job_data in all_jobs.values():
            job = Job.from_dict(json.loads(job_data))
            if status is None or job.status == status:
                jobs.append(job)
        
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)[:limit]
    
    async def get_stats(self) -> dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Queue stats
        """
        client = await self.get_client()
        
        all_jobs = await client.hgetall(self._jobs_hash)
        
        stats = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "total": len(all_jobs),
        }
        
        for job_data in all_jobs.values():
            job = Job.from_dict(json.loads(job_data))
            stats[job.status.value] = stats.get(job.status.value, 0) + 1
        
        return stats
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Global queue instances
default_queue = Queue("default")
agent_queue = Queue("agents")
workflow_queue = Queue("workflows")
