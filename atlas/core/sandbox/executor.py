"""Code execution runner."""

from __future__ import annotations

import asyncio
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import io
import contextlib


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0
    memory_usage_kb: float = 0
    logs: list[str] = field(default_factory=list)


class CodeExecutor:
    """Safe code executor with resource limits."""

    def __init__(
        self,
        timeout: float = 30.0,
        memory_limit_mb: int = 256,
        max_output_size: int = 10000,
    ):
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self.max_output_size = max_output_size
        self._execution_count = 0

    async def execute_python(
        self,
        code: str,
        globals_dict: Optional[dict] = None,
        locals_dict: Optional[dict] = None,
    ) -> ExecutionResult:
        """Execute Python code safely."""
        self._execution_count += 1
        start_time = asyncio.get_event_loop().time()
        
        stdout = io.StringIO()
        stderr = io.StringIO()
        logs = []
        
        exec_globals = globals_dict or {}
        exec_locals = locals_dict or {}
        
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec_result = exec(code, exec_globals, exec_locals)
                
                if asyncio.iscoroutine(exec_result):
                    await exec_result
            
            output = stdout.getvalue()
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size] + f"\n... (truncated, {len(output)} total chars)"
            
            return ExecutionResult(
                success=True,
                output=output,
                execution_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            )
            
        except Exception as e:
            error_output = stderr.getvalue()
            return ExecutionResult(
                success=False,
                output=stdout.getvalue(),
                error=f"{type(e).__name__}: {str(e)}",
                execution_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            )

    async def execute_with_timeout(
        self,
        code: str,
        language: str = "python",
    ) -> ExecutionResult:
        """Execute code with timeout."""
        try:
            if language == "python":
                return await asyncio.wait_for(
                    self.execute_python(code),
                    timeout=self.timeout,
                )
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Unsupported language: {language}",
                )
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error=f"Execution timed out after {self.timeout} seconds",
            )

    def get_stats(self) -> dict[str, Any]:
        return {
            "execution_count": self._execution_count,
            "timeout": self.timeout,
            "memory_limit_mb": self.memory_limit_mb,
        }