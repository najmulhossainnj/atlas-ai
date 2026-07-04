"""Python code execution tool."""

from __future__ import annotations

from typing import Any

from atlas.core.tools.base import BaseTool, ToolParameter, ToolResult
from atlas.core.sandbox.executor import CodeExecutor


class PythonExecTool(BaseTool):
    """Tool for executing Python code in a sandbox."""

    def __init__(
        self,
        timeout: float = 30.0,
        memory_limit_mb: int = 256,
    ):
        super().__init__(
            name="python_exec",
            description="Execute Python code in a sandboxed environment",
        )
        self.executor = CodeExecutor(timeout=timeout, memory_limit_mb=memory_limit_mb)
        self.register_parameters()

    def register_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="code",
            type="string",
            description="Python code to execute",
            required=True,
        ))
        self.add_parameter(ToolParameter(
            name="timeout",
            type="number",
            description="Timeout in seconds",
            required=False,
            default=30.0,
        ))

    async def execute(
        self,
        code: str,
        timeout: float = 30.0,
        **kwargs,
    ) -> ToolResult:
        """Execute Python code."""
        result = await self.executor.execute_with_timeout(
            code,
            language="python",
        )
        
        return ToolResult(
            success=result.success,
            data={
                "output": result.output,
                "execution_time_ms": result.execution_time_ms,
            },
            error=result.error,
        )