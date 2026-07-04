"""Planning engine with multiple strategies."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class PlanningStrategy(str, Enum):
    """Strategies for planning."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    GRAPH_PLANNING = "graph_planning"
    RECURSIVE_DECOMPOSITION = "recursive_decomposition"
    REFLECTION = "reflection"
    REPLANNING = "replanning"


@dataclass
class PlanStep:
    """A single step in a plan."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    action: str = ""
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None
    agent: Optional[str] = None
    tools: list[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    """A plan consisting of multiple steps."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    strategy: PlanningStrategy = PlanningStrategy.CHAIN_OF_THOUGHT
    status: str = "created"
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(
        self,
        description: str,
        action: str = "",
        dependencies: Optional[list[str]] = None,
        agent: Optional[str] = None,
        tools: Optional[list[str]] = None,
    ) -> PlanStep:
        """Add a step to the plan."""
        step = PlanStep(
            description=description,
            action=action,
            dependencies=dependencies or [],
            agent=agent,
            tools=tools or [],
        )
        self.steps.append(step)
        return step

    def get_ready_steps(self) -> list[PlanStep]:
        """Get steps that are ready to execute (dependencies met)."""
        completed_ids = {
            step.id for step in self.steps if step.status == "completed"
        }
        
        ready = []
        for step in self.steps:
            if step.status != "pending":
                continue
            
            deps_met = all(dep_id in completed_ids for dep_id in step.dependencies)
            if deps_met:
                ready.append(step)
        
        return ready

    def get_execution_order(self) -> list[PlanStep]:
        """Get steps in topologically sorted execution order."""
        order = []
        visited = set()
        step_map = {step.id: step for step in self.steps}

        def visit(step_id: str):
            if step_id in visited:
                return
            visited.add(step_id)
            
            step = step_map.get(step_id)
            if step:
                for dep_id in step.dependencies:
                    visit(dep_id)
                order.append(step)

        for step in self.steps:
            visit(step.id)

        return order

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "action": s.action,
                    "dependencies": s.dependencies,
                    "status": s.status,
                    "agent": s.agent,
                }
                for s in self.steps
            ],
            "strategy": self.strategy.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class PlanningEngine:
    """Engine for generating and executing plans."""

    def __init__(
        self,
        default_strategy: PlanningStrategy = PlanningStrategy.CHAIN_OF_THOUGHT,
        max_iterations: int = 10,
        reflection_enabled: bool = True,
    ):
        self.default_strategy = default_strategy
        self.max_iterations = max_iterations
        self.reflection_enabled = reflection_enabled
        self._plans: dict[str, Plan] = {}

    async def create_plan(
        self,
        goal: str,
        context: Optional[dict[str, Any]] = None,
        strategy: Optional[PlanningStrategy] = None,
    ) -> Plan:
        """Create a plan to achieve a goal."""
        strategy = strategy or self.default_strategy
        
        if strategy == PlanningStrategy.CHAIN_OF_THOUGHT:
            return await self._chain_of_thought(goal, context)
        elif strategy == PlanningStrategy.TREE_OF_THOUGHTS:
            return await self._tree_of_thoughts(goal, context)
        elif strategy == PlanningStrategy.RECURSIVE_DECOMPOSITION:
            return await self._recursive_decomposition(goal, context)
        else:
            return await self._chain_of_thought(goal, context)

    async def _chain_of_thought(
        self,
        goal: str,
        context: Optional[dict[str, Any]],
    ) -> Plan:
        """Generate a plan using chain of thought reasoning."""
        plan = Plan(
            goal=goal,
            strategy=PlanningStrategy.CHAIN_OF_THOUGHT,
        )

        plan.add_step(
            description=f"Understand the goal: {goal}",
            action="understand",
        )
        plan.add_step(
            description="Identify key requirements and constraints",
            action="analyze",
            dependencies=[plan.steps[0].id],
        )
        plan.add_step(
            description="Break down into actionable steps",
            action="decompose",
            dependencies=[plan.steps[1].id],
        )
        plan.add_step(
            description="Execute the plan",
            action="execute",
            dependencies=[plan.steps[2].id],
        )
        plan.add_step(
            description="Verify and validate results",
            action="verify",
            dependencies=[plan.steps[3].id],
        )

        self._plans[plan.id] = plan
        return plan

    async def _tree_of_thoughts(
        self,
        goal: str,
        context: Optional[dict[str, Any]],
    ) -> Plan:
        """Generate a plan using tree of thoughts reasoning."""
        plan = Plan(
            goal=goal,
            strategy=PlanningStrategy.TREE_OF_THOUGHTS,
        )

        plan.add_step(
            description=f"Explore multiple paths for: {goal}",
            action="explore_paths",
        )
        plan.add_step(
            description="Evaluate and compare paths",
            action="evaluate",
            dependencies=[plan.steps[0].id],
        )
        plan.add_step(
            description="Select the optimal path",
            action="select",
            dependencies=[plan.steps[1].id],
        )
        plan.add_step(
            description="Execute selected path",
            action="execute",
            dependencies=[plan.steps[2].id],
        )

        self._plans[plan.id] = plan
        return plan

    async def _recursive_decomposition(
        self,
        goal: str,
        context: Optional[dict[str, Any]],
    ) -> Plan:
        """Generate a plan using recursive task decomposition."""
        plan = Plan(
            goal=goal,
            strategy=PlanningStrategy.RECURSIVE_DECOMPOSITION,
        )

        root_step = plan.add_step(
            description=f"Achieve goal: {goal}",
            action="decompose",
        )

        await self._decompose_step(plan, root_step)

        self._plans[plan.id] = plan
        return plan

    async def _decompose_step(
        self,
        plan: Plan,
        step: PlanStep,
        depth: int = 0,
    ) -> None:
        """Recursively decompose a step into sub-steps."""
        if depth >= self.max_iterations:
            return

        sub_steps = [
            f"Subtask {i+1} for: {step.description}"
            for i in range(2)
        ]

        for i, sub_desc in enumerate(sub_steps):
            sub_step = plan.add_step(
                description=sub_desc,
                action="execute",
                dependencies=[step.id] if i == 0 else [plan.steps[-1].id],
            )
            
            if depth < 2:
                await self._decompose_step(plan, sub_step, depth + 1)

    async def reflect(
        self,
        plan: Plan,
        result: Any,
    ) -> dict[str, Any]:
        """Reflect on plan execution and generate insights."""
        if not self.reflection_enabled:
            return {"success": True, "lessons": []}

        completed_steps = [s for s in plan.steps if s.status == "completed"]
        failed_steps = [s for s in plan.steps if s.status == "failed"]

        return {
            "success": len(failed_steps) == 0,
            "completed_steps": len(completed_steps),
            "failed_steps": len(failed_steps),
            "lessons": [
                f"Completed {len(completed_steps)} steps successfully",
                f"Need to improve {len(failed_steps)} failed steps" if failed_steps else "All steps completed",
            ],
            "improvements": [
                "Consider parallel execution for independent steps",
                "Add more detailed error handling",
            ] if failed_steps else [],
        }

    async def replan(
        self,
        plan: Plan,
        failure_point: str,
        context: Optional[dict[str, Any]],
    ) -> Plan:
        """Create a new plan based on failure analysis."""
        new_plan = Plan(
            goal=plan.goal,
            strategy=PlanningStrategy.REPLANNING,
        )

        new_plan.add_step(
            description=f"Retry failed step: {failure_point}",
            action="retry",
        )
        new_plan.add_step(
            description="Adjust approach based on failure",
            action="adjust",
            dependencies=[new_plan.steps[0].id],
        )
        new_plan.add_step(
            description="Continue with revised plan",
            action="continue",
            dependencies=[new_plan.steps[1].id],
        )

        return new_plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by ID."""
        return self._plans.get(plan_id)

    def list_plans(self) -> list[Plan]:
        """List all plans."""
        return list(self._plans.values())

    async def update_step(
        self,
        plan_id: str,
        step_id: str,
        status: str,
        result: Optional[Any] = None,
    ) -> bool:
        """Update the status of a plan step."""
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        for step in plan.steps:
            if step.id == step_id:
                step.status = status
                if result is not None:
                    step.result = result
                if status == "completed":
                    step.completed_at = datetime.utcnow()
                return True

        return False
