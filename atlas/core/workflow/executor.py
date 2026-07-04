"""Workflow executor for managing complex workflows."""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import tenacity


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepType(str, Enum):
    """Types of workflow steps."""
    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    SEQUENCE = "sequence"
    APPROVAL = "approval"
    WAIT = "wait"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    step_type: WorkflowStepType = WorkflowStepType.TASK
    config: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 3600
    condition: Optional[str] = None
    loop_config: Optional[dict[str, Any]] = None
    parallel_config: Optional[dict[str, Any]] = None
    children: list[WorkflowStep] = field(default_factory=list)
    on_failure: Optional[str] = None
    on_success: Optional[str] = None


@dataclass
class WorkflowExecution:
    """Execution state of a workflow."""
    workflow_id: str = ""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkflowStatus = WorkflowStatus.CREATED
    current_step: Optional[str] = None
    step_results: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    checkpoint: Optional[str] = None


@dataclass
class Workflow:
    """A workflow definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: int = 1
    steps: list[WorkflowStep] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowExecutor:
    """Executes workflows with support for various patterns."""

    def __init__(
        self,
        max_concurrent: int = 10,
        checkpoint_enabled: bool = True,
        checkpoint_interval: int = 10,
    ):
        self.max_concurrent = max_concurrent
        self.checkpoint_enabled = checkpoint_enabled
        self.checkpoint_interval = checkpoint_interval
        self._workflows: dict[str, Workflow] = {}
        self._executions: dict[str, WorkflowExecution] = {}
        self._handlers: dict[str, Callable] = {}
        self._lock = asyncio.Lock()

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow definition."""
        self._workflows[workflow.id] = workflow

    def create_workflow(
        self,
        name: str,
        description: str = "",
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            name=name,
            description=description,
        )
        self._workflows[workflow.id] = workflow
        return workflow

    def add_step(
        self,
        workflow_id: str,
        step: WorkflowStep,
        parent_id: Optional[str] = None,
    ) -> None:
        """Add a step to a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if parent_id:
            parent = self._find_step(workflow.steps, parent_id)
            if parent:
                parent.children.append(step)
        else:
            workflow.steps.append(step)

    def _find_step(
        self,
        steps: list[WorkflowStep],
        step_id: str,
    ) -> Optional[WorkflowStep]:
        """Find a step by ID recursively."""
        for step in steps:
            if step.id == step_id:
                return step
            if step.children:
                found = self._find_step(step.children, step_id)
                if found:
                    return found
        return None

    async def execute(
        self,
        workflow_id: str,
        variables: Optional[dict[str, Any]] = None,
        start_from_checkpoint: bool = False,
    ) -> WorkflowExecution:
        """Execute a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            variables=variables or {},
        )

        if start_from_checkpoint and execution.checkpoint:
            execution.variables = await self._load_checkpoint(execution.checkpoint)

        self._executions[execution.execution_id] = execution
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.utcnow()

        try:
            for i, step in enumerate(workflow.steps):
                execution.current_step = step.id

                if self.checkpoint_enabled and i % self.checkpoint_interval == 0:
                    await self._save_checkpoint(execution)

                result = await self._execute_step(step, execution)
                execution.step_results[step.id] = result

            execution.status = WorkflowStatus.COMPLETED

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)

        finally:
            execution.completed_at = datetime.utcnow()
            if self.checkpoint_enabled:
                await self._clear_checkpoint(execution.execution_id)

        return execution

    async def _execute_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute a single workflow step."""
        try:
            if step.step_type == WorkflowStepType.TASK:
                return await self._execute_task(step, execution)
            elif step.step_type == WorkflowStepType.CONDITION:
                return await self._execute_condition(step, execution)
            elif step.step_type == WorkflowStepType.LOOP:
                return await self._execute_loop(step, execution)
            elif step.step_type == WorkflowStepType.PARALLEL:
                return await self._execute_parallel(step, execution)
            elif step.step_type == WorkflowStepType.SEQUENCE:
                return await self._execute_sequence(step, execution)
            elif step.step_type == WorkflowStepType.APPROVAL:
                return await self._execute_approval(step, execution)
            elif step.step_type == WorkflowStepType.WAIT:
                return await self._execute_wait(step, execution)
            else:
                return await self._execute_task(step, execution)

        except Exception as e:
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                return await self._execute_step(step, execution)
            if step.on_failure:
                return await self._handle_failure(step.on_failure, execution)
            raise

    async def _execute_task(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute a task step."""
        handler = self._handlers.get(step.config.get("handler", ""))
        
        if handler:
            return await handler(step.config, execution.variables)

        return {"status": "completed", "step": step.name}

    async def _execute_condition(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute a conditional step."""
        condition = step.condition
        if not condition:
            return {"branch": "default", "executed": False}

        condition_met = await self._evaluate_condition(condition, execution.variables)
        branch = "true" if condition_met else "false"

        child_steps = [
            c for c in step.children
            if c.config.get("branch") == branch or c.config.get("branch") == "default"
        ]

        results = []
        for child in child_steps:
            result = await self._execute_step(child, execution)
            results.append(result)

        return {"branch": branch, "executed": True, "results": results}

    async def _execute_loop(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute a loop step."""
        loop_config = step.loop_config or {}
        max_iterations = loop_config.get("max_iterations", 10)
        iterate_over = loop_config.get("iterate_over")

        results = []
        items = execution.variables.get(iterate_over, []) if iterate_over else range(max_iterations)

        for i, item in enumerate(items):
            if i >= max_iterations:
                break

            if iterate_over:
                execution.variables["current_item"] = item
                execution.variables["loop_index"] = i

            for child in step.children:
                result = await self._execute_step(child, execution)
                results.append(result)

        return {"iterations": len(results), "results": results}

    async def _execute_parallel(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute parallel steps."""
        parallel_config = step.parallel_config or {}
        max_concurrent = parallel_config.get("max_concurrent", self.max_concurrent)

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_limit(child: WorkflowStep) -> tuple[str, Any]:
            async with semaphore:
                return child.id, await self._execute_step(child, execution)

        tasks = [execute_with_limit(child) for child in step.children]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "completed": len([r for r in results if not isinstance(r, Exception)]),
            "failed": len([r for r in results if isinstance(r, Exception)]),
            "results": results,
        }

    async def _execute_sequence(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute a sequence of steps."""
        results = []
        for child in step.children:
            result = await self._execute_step(child, execution)
            results.append(result)
        return {"results": results}

    async def _execute_approval(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute an approval step (requires human input)."""
        approval_config = step.config.get("approval", {})
        timeout = approval_config.get("timeout", 3600)
        approver = approval_config.get("approver", "system")

        return {
            "status": "pending_approval",
            "approver": approver,
            "timeout": timeout,
            "step": step.name,
        }

    async def _execute_wait(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
    ) -> Any:
        """Execute a wait step."""
        wait_config = step.config.get("wait", {})
        duration = wait_config.get("duration", 60)

        await asyncio.sleep(duration)

        return {"status": "completed", "waited": duration}

    async def _evaluate_condition(
        self,
        condition: str,
        variables: dict[str, Any],
    ) -> bool:
        """Evaluate a condition expression."""
        try:
            safe_vars = {k: v for k, v in variables.items() if not k.startswith("_")}
            return eval(condition, {"__builtins__": {}}, safe_vars)
        except Exception:
            return False

    async def _handle_failure(
        self,
        failure_handler: str,
        execution: WorkflowExecution,
    ) -> Any:
        """Handle step failure."""
        if failure_handler in self._handlers:
            return await self._handlers[failure_handler](execution.variables)
        return {"status": "failed", "handler": failure_handler}

    async def _save_checkpoint(self, execution: WorkflowExecution) -> None:
        """Save a checkpoint for recovery."""
        execution.checkpoint = json.dumps({
            "step_results": execution.step_results,
            "variables": execution.variables,
            "current_step": execution.current_step,
        })

    async def _load_checkpoint(self, checkpoint_data: str) -> dict[str, Any]:
        """Load a checkpoint for recovery."""
        data = json.loads(checkpoint_data)
        return data.get("variables", {})

    async def _clear_checkpoint(self, execution_id: str) -> None:
        """Clear a checkpoint after completion."""
        execution = self._executions.get(execution_id)
        if execution:
            execution.checkpoint = None

    def register_handler(self, name: str, handler: Callable) -> None:
        """Register a handler function for workflow steps."""
        self._handlers[name] = handler

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get an execution by ID."""
        return self._executions.get(execution_id)

    def list_executions(self, workflow_id: Optional[str] = None) -> list[WorkflowExecution]:
        """List workflow executions."""
        if workflow_id:
            return [
                e for e in self._executions.values()
                if e.workflow_id == workflow_id
            ]
        return list(self._executions.values())

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return False

        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            return True

        return False
