"""Agent orchestrator for managing multi-agent workflows."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from atlas.core.agents.base import (
    Agent,
    AgentConfig,
    AgentMessage,
    AgentStatus,
    MessageRole,
)


class OrchestrationMode(str, Enum):
    """Modes for orchestrating agents."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"


@dataclass
class Task:
    """A task to be executed by an agent."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assigned_agent: Optional[str] = None
    status: AgentStatus = AgentStatus.IDLE
    result: Optional[Any] = None
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class AgentRegistry:
    """Registry for managing agents."""
    agents: dict[str, Agent] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def register(self, agent: Agent) -> None:
        """Register a new agent."""
        async with self._lock:
            self.agents[agent.id] = agent

    async def unregister(self, agent_id: str) -> None:
        """Unregister an agent."""
        async with self._lock:
            self.agents.pop(agent_id, None)

    async def get(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        async with self._lock:
            return self.agents.get(agent_id)

    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        async with self._lock:
            for agent in self.agents.values():
                if agent.name == name:
                    return agent
            return None

    async def list_agents(self) -> list[Agent]:
        """List all registered agents."""
        async with self._lock:
            return list(self.agents.values())


class AgentOrchestrator:
    """Orchestrates multiple agents to accomplish complex tasks."""

    def __init__(
        self,
        mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL,
        max_concurrent: int = 5,
    ):
        self.mode = mode
        self.max_concurrent = max_concurrent
        self.registry = AgentRegistry()
        self.tasks: dict[str, Task] = {}
        self.execution_graph: dict[str, list[str]] = {}
        self._running_tasks: set[str] = set()
        self._lock = asyncio.Lock()
        self._event_callbacks: list[Callable] = []

    async def register_agent(self, agent: Agent) -> str:
        """Register an agent with the orchestrator."""
        await self.registry.register(agent)
        return agent.id

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the orchestrator."""
        await self.registry.unregister(agent_id)

    async def create_task(
        self,
        description: str,
        agent_name: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            description=description,
            assigned_agent=agent_name,
            dependencies=dependencies or [],
        )
        self.tasks[task.id] = task
        
        if task.dependencies:
            for dep_id in task.dependencies:
                if dep_id not in self.execution_graph:
                    self.execution_graph[dep_id] = []
                self.execution_graph[dep_id].append(task.id)

        await self._emit_event("task_created", {"task_id": task.id, "description": description})
        return task

    async def execute_task(self, task_id: str) -> Any:
        """Execute a single task with an agent."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = AgentStatus.EXECUTING
        task.started_at = datetime.utcnow()
        await self._emit_event("task_started", {"task_id": task_id})

        try:
            agent = None
            if task.assigned_agent:
                agent = await self.registry.get_by_name(task.assigned_agent)
            
            if not agent:
                agent = await self._select_agent(task)

            result = await agent.run(task.description)
            task.result = result.content
            task.status = AgentStatus.FINISHED
            task.completed_at = datetime.utcnow()
            
            await self._emit_event("task_completed", {
                "task_id": task_id,
                "result": result.content,
            })
            
            return result.content

        except Exception as e:
            task.status = AgentStatus.ERROR
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            
            await self._emit_event("task_error", {
                "task_id": task_id,
                "error": str(e),
            })
            raise

    async def execute_workflow(
        self,
        tasks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute a workflow of tasks."""
        created_tasks = []
        
        for task_def in tasks:
            task = await self.create_task(
                description=task_def.get("description", ""),
                agent_name=task_def.get("agent"),
                dependencies=task_def.get("dependencies", []),
            )
            created_tasks.append(task)

        if self.mode == OrchestrationMode.SEQUENTIAL:
            return await self._execute_sequential(created_tasks)
        elif self.mode == OrchestrationMode.PARALLEL:
            return await self._execute_parallel(created_tasks)
        elif self.mode == OrchestrationMode.HIERARCHICAL:
            return await self._execute_hierarchical(created_tasks)
        else:
            return await self._execute_collaborative(created_tasks)

    async def _execute_sequential(self, tasks: list[Task]) -> dict[str, Any]:
        """Execute tasks sequentially."""
        results = {}
        for task in tasks:
            result = await self.execute_task(task.id)
            results[task.id] = result
        return results

    async def _execute_parallel(self, tasks: list[Task]) -> dict[str, Any]:
        """Execute independent tasks in parallel."""
        async def execute_with_tracking(task: Task) -> tuple[str, Any]:
            async with self._lock:
                if task.id in self._running_tasks:
                    return task.id, None
                self._running_tasks.add(task.id)
            
            try:
                result = await self.execute_task(task.id)
                return task.id, result
            finally:
                async with self._lock:
                    self._running_tasks.discard(task.id)

        ready_tasks = self._get_ready_tasks(tasks)
        results = {}
        
        while ready_tasks or self._running_tasks:
            batch = ready_tasks[:self.max_concurrent]
            ready_tasks = ready_tasks[self.max_concurrent:]
            
            task_results = await asyncio.gather(
                *[execute_with_tracking(t) for t in batch],
                return_exceptions=True,
            )
            
            for task_id, result in task_results:
                if isinstance(result, Exception):
                    results[task_id] = {"error": str(result)}
                else:
                    results[task_id] = result

            ready_tasks = self._get_ready_tasks(list(self.tasks.values()))

        return results

    async def _execute_hierarchical(self, tasks: list[Task]) -> dict[str, Any]:
        """Execute tasks hierarchically with a planner agent."""
        planner_agent = await self.registry.get_by_name("General Planner")
        
        if not planner_agent:
            return await self._execute_sequential(tasks)

        workflow_description = "\n".join([
            f"{i+1}. {t.description}" for i, t in enumerate(tasks)
        ])
        
        plan_result = await planner_agent.run(
            f"Create an execution plan for the following tasks:\n{workflow_description}"
        )

        task_map = {t.description: t.id for t in tasks}
        
        execution_order = self._parse_plan(plan_result.content, task_map)
        
        results = {}
        for task_id in execution_order:
            if task_id in task_map.values():
                results[task_id] = await self.execute_task(task_id)

        return results

    async def _execute_collaborative(self, tasks: list[Task]) -> dict[str, Any]:
        """Execute tasks with agent collaboration."""
        async def agent_loop(agent: Agent, agent_tasks: list[Task]):
            for task in agent_tasks:
                if task.assigned_agent == agent.name:
                    await self.execute_task(task.id)

        agents = await self.registry.list_agents()
        
        if not agents:
            return await self._execute_sequential(tasks)

        tasks_per_agent = [[] for _ in agents]
        for task in tasks:
            for i, agent in enumerate(agents):
                if task.assigned_agent == agent.name:
                    tasks_per_agent[i].append(task)
                    break

        await asyncio.gather(
            *[agent_loop(agent, tasks) for agent, tasks in zip(agents, tasks_per_agent)]
        )

        return {task.id: task.result for task in tasks}

    def _get_ready_tasks(self, tasks: list[Task]) -> list[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in tasks:
            if task.status != AgentStatus.IDLE:
                continue
            
            deps_met = all(
                self.tasks.get(dep_id, Task()).status == AgentStatus.FINISHED
                for dep_id in task.dependencies
            )
            
            if deps_met:
                ready.append(task)
        
        return ready

    def _parse_plan(
        self,
        plan_text: str,
        task_map: dict[str, str],
    ) -> list[str]:
        """Parse a plan text into ordered task IDs."""
        lines = plan_text.strip().split("\n")
        ordered_ids = []
        
        for line in lines:
            for desc, task_id in task_map.items():
                if desc.lower() in line.lower():
                    if task_id not in ordered_ids:
                        ordered_ids.append(task_id)
        
        return ordered_ids

    async def _select_agent(self, task: Task) -> Agent:
        """Select an appropriate agent for a task."""
        agents = await self.registry.list_agents()
        
        if not agents:
            raise RuntimeError("No agents available")
        
        return agents[0]

    def on_event(self, callback: Callable) -> None:
        """Register a callback for orchestrator events."""
        self._event_callbacks.append(callback)

    async def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event to all registered callbacks."""
        event = {"type": event_type, "data": data, "timestamp": datetime.utcnow().isoformat()}
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception:
                pass

    async def get_status(self) -> dict[str, Any]:
        """Get the current status of the orchestrator."""
        task_counts = {
            "total": len(self.tasks),
            "idle": sum(1 for t in self.tasks.values() if t.status == AgentStatus.IDLE),
            "executing": sum(1 for t in self.tasks.values() if t.status == AgentStatus.EXECUTING),
            "finished": sum(1 for t in self.tasks.values() if t.status == AgentStatus.FINISHED),
            "error": sum(1 for t in self.tasks.values() if t.status == AgentStatus.ERROR),
        }
        
        return {
            "mode": self.mode.value,
            "tasks": task_counts,
            "registered_agents": len(self.registry.agents),
            "running_tasks": len(self._running_tasks),
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == AgentStatus.EXECUTING:
            task.status = AgentStatus.IDLE
            return True
        
        return False
