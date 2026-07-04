"""Base tool classes and configuration."""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json


class ToolCategory(str, Enum):
    """Categories of tools."""
    FILESYSTEM = "filesystem"
    VERSION_CONTROL = "version_control"
    EXECUTION = "execution"
    NETWORK = "network"
    DATA = "data"
    AUTOMATION = "automation"
    AI = "ai"
    CUSTOM = "custom"


@dataclass
class ToolConfig:
    """Configuration for a tool."""
    name: str
    description: str
    category: ToolCategory = ToolCategory.CUSTOM
    parameters: dict[str, Any] = field(default_factory=dict)
    timeout: int = 60
    retries: int = 3
    sandboxed: bool = True
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_name: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "timestamp": self.timestamp.isoformat(),
        }


class Tool(ABC):
    """Base class for all tools in Atlas."""

    def __init__(self, config: Optional[ToolConfig] = None):
        self.config = config or ToolConfig(
            name=self.__class__.__name__,
            description="Base tool",
        )
        self.id = str(uuid.uuid4())
        self._lock = asyncio.Lock()
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._errors = 0

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def description(self) -> str:
        return self.config.description

    @property
    def schema(self) -> dict[str, Any]:
        """Return the JSON schema for the tool's parameters."""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "parameters": self.config.parameters,
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given parameters."""
        pass

    async def run(self, **kwargs: Any) -> ToolResult:
        """Run the tool with timing, retries, and error handling."""
        start_time = datetime.utcnow()
        result = ToolResult(
            tool_name=self.name,
            parameters=kwargs,
        )

        async with self._lock:
            self._execution_count += 1

        for attempt in range(max(1, self.config.retries)):
            try:
                result = await self._execute_with_timeout(
                    self.execute(**kwargs),
                    timeout=self.config.timeout,
                )

                if result.success:
                    return result

                if attempt < self.config.retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except asyncio.TimeoutError:
                result.success = False
                result.error = f"Tool execution timed out after {self.config.timeout}s"
            except Exception as e:
                result.success = False
                result.error = str(e)
                async with self._lock:
                    self._errors += 1

        end_time = datetime.utcnow()
        result.execution_time = (end_time - start_time).total_seconds()
        async with self._lock:
            self._total_execution_time += result.execution_time

        return result

    async def _execute_with_timeout(
        self,
        coro: Any,
        timeout: int,
    ) -> ToolResult:
        """Execute a coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise

    def validate_parameters(self, parameters: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool parameters against the schema."""
        required = self.config.parameters.get("required", [])
        
        for param in required:
            if param not in parameters:
                return False, f"Missing required parameter: {param}"
        
        return True, None

    def get_stats(self) -> dict[str, Any]:
        """Get tool execution statistics."""
        return {
            "name": self.name,
            "category": self.config.category.value,
            "executions": self._execution_count,
            "total_time": self._total_execution_time,
            "avg_time": (
                self._total_execution_time / self._execution_count
                if self._execution_count > 0 else 0
            ),
            "errors": self._errors,
            "error_rate": (
                self._errors / self._execution_count
                if self._execution_count > 0 else 0
            ),
        }


class ToolExecutor:
    """Executes tools with resource limits and sandboxing."""

    def __init__(
        self,
        enable_sandboxing: bool = True,
        max_concurrent: int = 10,
        default_timeout: int = 60,
    ):
        self.enable_sandboxing = enable_sandboxing
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self._running_tasks: set[asyncio.Task] = set()
        self._lock = asyncio.Lock()

    async def execute(
        self,
        tool: Tool,
        parameters: dict[str, Any],
        sandbox: bool = True,
    ) -> ToolResult:
        """Execute a tool with optional sandboxing."""
        is_valid, error = tool.validate_parameters(parameters)
        if not is_valid:
            return ToolResult(
                success=False,
                error=error,
                tool_name=tool.name,
                parameters=parameters,
            )

        if sandbox and self.enable_sandboxing and tool.config.sandboxed:
            return await self._execute_sandboxed(tool, parameters)
        
        return await tool.run(**parameters)

    async def _execute_sandboxed(
        self,
        tool: Tool,
        parameters: dict[str, Any],
    ) -> ToolResult:
        """Execute a tool in a sandboxed environment."""
        return await tool.run(**parameters)

    async def execute_batch(
        self,
        tools_and_params: list[tuple[Tool, dict[str, Any]]],
    ) -> list[ToolResult]:
        """Execute multiple tools concurrently."""
        tasks = []
        
        async def execute_one(tool: Tool, params: dict[str, Any]) -> ToolResult:
            return await self.execute(tool, params)

        for tool, params in tools_and_params:
            task = asyncio.create_task(execute_one(tool, params))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r if isinstance(r, ToolResult) else ToolResult(
                success=False,
                error=str(r),
            )
            for r in results
        ]
