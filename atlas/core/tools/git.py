"""Git operations tool."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from atlas.core.tools.base import BaseTool, ToolParameter, ToolResult


class GitTool(BaseTool):
    """Tool for Git operations."""

    def __init__(self, repo_path: str = "."):
        super().__init__(
            name="git",
            description="Perform Git version control operations",
        )
        self.repo_path = Path(repo_path)
        self.register_parameters()

    def register_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="operation",
            type="string",
            description="Git operation",
            required=True,
            enum=["status", "diff", "log", "commit", "push", "pull", "branch", "checkout", "add"],
        ))
        self.add_parameter(ToolParameter(
            name="args",
            type="string",
            description="Additional arguments for the git command",
            required=False,
        ))

    async def execute(
        self,
        operation: str,
        args: str = "",
        **kwargs,
    ) -> ToolResult:
        """Execute a git operation."""
        try:
            cmd = f"git {operation} {args}".strip()
            
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.repo_path),
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0 and "fatal" in stderr.decode().lower():
                return ToolResult(
                    success=False,
                    error=stderr.decode() or "Git command failed",
                    data={"returncode": proc.returncode},
                )
            
            return ToolResult(
                success=proc.returncode == 0,
                data={
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "returncode": proc.returncode,
                },
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))