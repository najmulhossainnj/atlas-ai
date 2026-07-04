"""Base Agent class and configuration."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import uuid

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent lifecycle status."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    FINISHED = "finished"
    ERROR = "error"
    PAUSED = "paused"


class AgentType(str, Enum):
    """Types of agents available in Atlas."""
    GENERAL_PLANNER = "general_planner"
    RESEARCH = "research"
    SOFTWARE_ENGINEER = "software_engineer"
    REVIEWER = "reviewer"
    BROWSER = "browser"
    DATA = "data"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    QUANT_RESEARCH = "quant_research"
    MARKET_MAKING = "market_making"
    RISK_MANAGEMENT = "risk_management"
    CUSTOM = "custom"


class MessageRole(str, Enum):
    """Message roles in agent communication."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"
    TOOL = "tool"


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = MessageRole.ASSISTANT
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reply_to: Optional[str] = None
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to,
            "references": self.references,
        }


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""
    name: str
    role: str
    goal: str
    agent_type: AgentType = AgentType.CUSTOM
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    max_iterations: int = 100
    max_tokens: int = 128_000
    timeout_seconds: int = 3600
    budget: float = 100.0
    temperature: float = 0.7
    model: Optional[str] = None
    memory_enabled: bool = True
    planning_enabled: bool = True
    reflection_enabled: bool = True
    callbacks: Optional[dict[str, Callable]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionMetrics:
    """Track agent execution metrics."""
    iterations: int = 0
    tokens_used: int = 0
    cost: float = 0.0
    tool_calls: int = 0
    errors: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0


@dataclass
class ExecutionContext:
    """Runtime context for agent execution."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    child_task_ids: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Base class for all agents in Atlas."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = str(uuid.uuid4())
        self.status = AgentStatus.IDLE
        self.messages: list[AgentMessage] = []
        self.context = ExecutionContext()
        self.metrics = ExecutionMetrics()
        self._running = False
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> str:
        return self.config.role

    @abstractmethod
    async def think(self, message: AgentMessage) -> AgentMessage:
        """Main thinking/reasoning method - to be implemented by subclasses."""
        pass

    @abstractmethod
    async def execute(self, message: AgentMessage) -> AgentMessage:
        """Main execution method - to be implemented by subclasses."""
        pass

    async def plan(self, goal: str) -> list[dict[str, Any]]:
        """Create a plan to achieve the goal."""
        return [{"step": 1, "action": "execute", "description": goal}]

    async def reflect(self, result: Any) -> dict[str, Any]:
        """Reflect on the execution result."""
        return {
            "success": True,
            "lessons_learned": [],
            "improvements": [],
        }

    async def run(self, input_message: str) -> AgentMessage:
        """Main entry point for running the agent."""
        async with self._lock:
            if self._running:
                raise RuntimeError(f"Agent {self.name} is already running")
            self._running = True

        self.metrics.start_time = datetime.utcnow()
        self.status = AgentStatus.EXECUTING

        try:
            user_message = AgentMessage(
                role=MessageRole.USER,
                content=input_message,
            )
            self.messages.append(user_message)

            response = await self.execute(user_message)
            self.messages.append(response)

            self.metrics.iterations += 1
            self.status = AgentStatus.FINISHED

            return response

        except Exception as e:
            self.metrics.errors += 1
            self.status = AgentStatus.ERROR
            return AgentMessage(
                role=MessageRole.ASSISTANT,
                content=f"Error: {str(e)}",
                metadata={"error": True},
            )
        finally:
            self._running = False
            self.metrics.end_time = datetime.utcnow()
            if self.metrics.start_time:
                delta = self.metrics.end_time - self.metrics.start_time
                self.metrics.total_duration_seconds = delta.total_seconds()

    async def stop(self) -> None:
        """Stop the agent's execution."""
        async with self._lock:
            self._running = False
            self.status = AgentStatus.PAUSED

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the conversation history."""
        self.messages.append(message)

    def get_messages(self, role: Optional[MessageRole] = None) -> list[AgentMessage]:
        """Get messages, optionally filtered by role."""
        if role is None:
            return self.messages.copy()
        return [m for m in self.messages if m.role == role]

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.messages.clear()

    def to_dict(self) -> dict[str, Any]:
        """Serialize agent state to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "status": self.status.value,
            "agent_type": self.config.agent_type.value,
            "config": {
                "goal": self.config.goal,
                "skills": self.config.skills,
                "tools": self.config.tools,
                "max_iterations": self.config.max_iterations,
            },
            "metrics": {
                "iterations": self.metrics.iterations,
                "tokens_used": self.metrics.tokens_used,
                "cost": self.metrics.cost,
                "tool_calls": self.metrics.tool_calls,
                "errors": self.metrics.errors,
            },
            "message_count": len(self.messages),
        }
