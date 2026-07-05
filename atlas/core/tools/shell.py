"""Shell command execution tool."""

from __future__ import annotations

import asyncio
import shlex
from typing import Any, Optional

from atlas.core.tools.base import BaseTool, ToolParameter, ToolResult


class ShellTool(BaseTool):
    """Tool for executing shell commands."""

    def __init__(
        self,
        working_dir: str = ".",
        timeout: int = 30,
        allowed_commands: Optional[list[str]] = None,
    ):
        super().__init__(
            name="shell",
            description="Execute shell commands",
        )
        self.working_dir = working_dir
        self.timeout = timeout
        self.allowed_commands = allowed_commands
        self.register_parameters()

    def register_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="command",
            type="string",
            description="Shell command to execute",
            required=True,
        ))
        self.add_parameter(ToolParameter(
            name="timeout",
            type="integer",
            description="Timeout in seconds",
            required=False,
            default=30,
        ))

    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed."""
        if not self.allowed_commands:
            return True
        cmd_parts = shlex.split(command)
        if cmd_parts:
            return cmd_parts[0] in self.allowed_commands
        return True

    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute a shell command."""
        if not self._is_command_allowed(command):
            return ToolResult(
                success=False,
                error=f"Command not allowed: {command.split()[0] if command else 'empty'}",
            )

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )

            cmd_timeout = timeout or self.timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=cmd_timeout,
                )
                return ToolResult(
                    success=proc.returncode == 0,
                    data={
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else "",
                        "returncode": proc.returncode,
                    },
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {cmd_timeout} seconds",
                )

        except Exception as e:
            return ToolResult(success=False, error=str(e))