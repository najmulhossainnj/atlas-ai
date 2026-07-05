"""Execution replay storage for debugging and analysis."""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import os


class ExecutionStatus(str, Enum):
    """Status of an execution."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ExecutionStep:
    """A single step in an execution."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    action: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionReplay:
    """Complete replay of an agent execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    agent_name: str = ""
    task: str = ""
    status: ExecutionStatus = ExecutionStatus.RUNNING
    steps: list[ExecutionStep] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metrics: dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ExecutionStep) -> None:
        self.steps.append(step)

    def add_message(self, message: dict[str, Any]) -> None:
        self.messages.append(message)

    def add_tool_call(self, tool_call: dict[str, Any]) -> None:
        self.tool_calls.append(tool_call)

    def complete(self, status: ExecutionStatus = ExecutionStatus.COMPLETED) -> None:
        self.status = status
        self.end_time = datetime.utcnow()
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_ms = delta.total_seconds() * 1000

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "task": self.task,
            "status": self.status.value,
            "steps": [
                {
                    "step_id": s.step_id,
                    "name": s.name,
                    "action": s.action,
                    "input_data": s.input_data,
                    "output_data": s.output_data,
                    "error": s.error,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "duration_ms": s.duration_ms,
                    "metadata": s.metadata,
                }
                for s in self.steps
            ],
            "messages": self.messages,
            "tool_calls": self.tool_calls,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "metrics": self.metrics,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionReplay:
        replay = cls(
            id=data.get("id", str(uuid.uuid4())),
            agent_id=data.get("agent_id", ""),
            agent_name=data.get("agent_name", ""),
            task=data.get("task", ""),
            status=ExecutionStatus(data.get("status", ExecutionStatus.RUNNING)),
            messages=data.get("messages", []),
            tool_calls=data.get("tool_calls", []),
            start_time=datetime.fromisoformat(data["start_time"]) if "start_time" in data else datetime.utcnow(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration_ms=data.get("duration_ms"),
            metrics=data.get("metrics", {}),
            trace_id=data.get("trace_id"),
            metadata=data.get("metadata", {}),
        )
        
        for step_data in data.get("steps", []):
            step = ExecutionStep(
                step_id=step_data.get("step_id", str(uuid.uuid4())),
                name=step_data.get("name", ""),
                action=step_data.get("action", ""),
                input_data=step_data.get("input_data", {}),
                output_data=step_data.get("output_data"),
                error=step_data.get("error"),
                start_time=datetime.fromisoformat(step_data["start_time"]) if "start_time" in step_data else datetime.utcnow(),
                end_time=datetime.fromisoformat(step_data["end_time"]) if step_data.get("end_time") else None,
                duration_ms=step_data.get("duration_ms"),
                metadata=step_data.get("metadata", {}),
            )
            replay.steps.append(step)
        
        return replay


class ReplayStore:
    """Storage for execution replays."""

    def __init__(
        self,
        storage_path: str = "./data/replays",
        max_replays: int = 1000,
    ):
        self.storage_path = storage_path
        self.max_replays = max_replays
        self._replays: dict[str, ExecutionReplay] = {}
        self._by_agent: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()
        os.makedirs(storage_path, exist_ok=True)

    async def save(self, replay: ExecutionReplay) -> None:
        """Save an execution replay."""
        async with self._lock:
            self._replays[replay.id] = replay
            
            if replay.agent_id not in self._by_agent:
                self._by_agent[replay.agent_id] = []
            if replay.id not in self._by_agent[replay.agent_id]:
                self._by_agent[replay.agent_id].append(replay.id)
            
            await self._persist_replay(replay)

    async def get(self, replay_id: str) -> Optional[ExecutionReplay]:
        """Get a replay by ID."""
        async with self._lock:
            replay = self._replays.get(replay_id)
            if replay:
                return replay
            
            replay = await self._load_replay(replay_id)
            if replay:
                self._replays[replay.id] = replay
            return replay

    async def list_replays(
        self,
        agent_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 100,
    ) -> list[ExecutionReplay]:
        """List replays with optional filters."""
        async with self._lock:
            replays = list(self._replays.values())
        
        if agent_id:
            replays = [r for r in replays if r.agent_id == agent_id]
        if status:
            replays = [r for r in replays if r.status == status]
        
        replays.sort(key=lambda r: r.start_time, reverse=True)
        return replays[:limit]

    async def delete(self, replay_id: str) -> bool:
        """Delete a replay."""
        async with self._lock:
            replay = self._replays.pop(replay_id, None)
            if not replay:
                return False
            
            if replay.agent_id in self._by_agent:
                self._by_agent[replay.agent_id].remove(replay_id)
            
            filepath = os.path.join(self.storage_path, f"{replay_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return True

    async def cleanup_old(self, days: int = 30) -> int:
        """Clean up replays older than specified days."""
        cutoff = datetime.utcnow().timestamp() - (days * 86400)
        deleted = 0
        
        async with self._lock:
            to_delete = []
            for replay_id, replay in self._replays.items():
                if replay.start_time.timestamp() < cutoff:
                    to_delete.append(replay_id)
            
            for replay_id in to_delete:
                replay = self._replays.pop(replay_id, None)
                if replay:
                    if replay.agent_id in self._by_agent:
                        self._by_agent[replay.agent_id].discard(replay_id)
                    deleted += 1
        
        return deleted

    async def get_stats(self) -> dict[str, Any]:
        """Get replay store statistics."""
        async with self._lock:
            status_counts = {}
            for replay in self._replays.values():
                status = replay.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_replays": len(self._replays),
                "by_status": status_counts,
                "by_agent": len(self._by_agent),
                "storage_path": self.storage_path,
                "max_replays": self.max_replays,
            }

    async def _persist_replay(self, replay: ExecutionReplay) -> None:
        """Persist a replay to disk."""
        filepath = os.path.join(self.storage_path, f"{replay.id}.json")
        async with asyncio.Lock():
            with open(filepath, "w") as f:
                f.write(json.dumps(replay.to_dict(), default=str))

    async def _load_replay(self, replay_id: str) -> Optional[ExecutionReplay]:
        """Load a replay from disk."""
        filepath = os.path.join(self.storage_path, f"{replay_id}.json")
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return ExecutionReplay.from_dict(data)
        except Exception:
            return None


class ExecutionRecorder:
    """Context manager for recording agent executions."""

    def __init__(
        self,
        store: Optional[ReplayStore] = None,
        agent_id: str = "",
        agent_name: str = "",
    ):
        self.store = store or ReplayStore()
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.replay: Optional[ExecutionReplay] = None
        self._current_step: Optional[ExecutionStep] = None

    async def start(self, task: str, trace_id: Optional[str] = None) -> ExecutionReplay:
        """Start recording an execution."""
        self.replay = ExecutionReplay(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            task=task,
            trace_id=trace_id,
        )
        await self.store.save(self.replay)
        return self.replay

    async def add_step(
        self,
        name: str,
        action: str = "",
        input_data: Optional[dict[str, Any]] = None,
    ) -> ExecutionStep:
        """Add a step to the recording."""
        step = ExecutionStep(
            name=name,
            action=action,
            input_data=input_data or {},
        )
        if self.replay:
            self.replay.add_step(step)
        self._current_step = step
        return step

    async def complete_step(
        self,
        output_data: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Complete the current step."""
        if self._current_step and self.replay:
            self._current_step.end_time = datetime.utcnow()
            self._current_step.output_data = output_data
            self._current_step.error = error
            if self._current_step.start_time:
                delta = self._current_step.end_time - self._current_step.start_time
                self._current_step.duration_ms = delta.total_seconds() * 1000
            await self.store.save(self.replay)
        self._current_step = None

    async def add_message(self, role: str, content: str) -> None:
        """Add a message to the recording."""
        if self.replay:
            self.replay.add_message({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            })

    async def add_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: Any,
        duration_ms: float = 0,
    ) -> None:
        """Add a tool call to the recording."""
        if self.replay:
            self.replay.add_tool_call({
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
            })

    async def complete(
        self,
        status: ExecutionStatus = ExecutionStatus.COMPLETED,
        metrics: Optional[dict[str, Any]] = None,
    ) -> ExecutionReplay:
        """Complete the recording."""
        if self.replay:
            self.replay.complete(status)
            if metrics:
                self.replay.metrics = metrics
            await self.store.save(self.replay)
        return self.replay
