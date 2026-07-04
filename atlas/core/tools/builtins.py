"""Built-in tools for Atlas."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from typing import Any, Optional

from atlas.core.tools.base import Tool, ToolConfig, ToolResult, ToolCategory


class FilesystemTool(Tool):
    """Tool for filesystem operations."""

    def __init__(self):
        super().__init__(
            ToolConfig(
                name="filesystem",
                description="Perform filesystem operations like read, write, list, delete",
                category=ToolCategory.FILESYSTEM,
                parameters={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "list", "delete", "mkdir", "exists", "copy", "move"],
                            "description": "The filesystem operation to perform",
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory path",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write (for write operation)",
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Recursive operation (for list, delete)",
                        },
                    },
                    "required": ["operation", "path"],
                },
                sandboxed=True,
                permissions=["fs:read", "fs:write"],
            )
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation")
        path = kwargs.get("path")
        content = kwargs.get("content")
        recursive = kwargs.get("recursive", False)

        try:
            if operation == "read":
                async with asyncio.Lock():
                    with open(path, "r") as f:
                        content = f.read()
                return ToolResult(
                    success=True,
                    output=content,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "write":
                async with asyncio.Lock():
                    with open(path, "w") as f:
                        f.write(content or "")
                return ToolResult(
                    success=True,
                    output=f"Written to {path}",
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "list":
                if recursive:
                    items = []
                    for root, dirs, files in os.walk(path):
                        for name in files:
                            items.append(os.path.join(root, name))
                        for name in dirs:
                            items.append(os.path.join(root, name) + "/")
                else:
                    items = os.listdir(path)
                return ToolResult(
                    success=True,
                    output=items,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "delete":
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path) and recursive:
                    import shutil
                    shutil.rmtree(path)
                return ToolResult(
                    success=True,
                    output=f"Deleted {path}",
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "mkdir":
                os.makedirs(path, exist_ok=True)
                return ToolResult(
                    success=True,
                    output=f"Created directory {path}",
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "exists":
                return ToolResult(
                    success=True,
                    output=os.path.exists(path),
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "copy":
                import shutil
                dest = kwargs.get("destination")
                shutil.copy2(path, dest)
                return ToolResult(
                    success=True,
                    output=f"Copied {path} to {dest}",
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "move":
                import shutil
                dest = kwargs.get("destination")
                shutil.move(path, dest)
                return ToolResult(
                    success=True,
                    output=f"Moved {path} to {dest}",
                    tool_name=self.name,
                    parameters=kwargs,
                )

            return ToolResult(
                success=False,
                error=f"Unknown operation: {operation}",
                tool_name=self.name,
                parameters=kwargs,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=self.name,
                parameters=kwargs,
            )


class GitTool(Tool):
    """Tool for Git version control operations."""

    def __init__(self):
        super().__init__(
            ToolConfig(
                name="git",
                description="Perform Git operations like clone, commit, push, pull, branch",
                category=ToolCategory.VERSION_CONTROL,
                parameters={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["clone", "commit", "push", "pull", "branch", "status", "log", "diff", "checkout", "add"],
                            "description": "The Git operation to perform",
                        },
                        "repo_url": {
                            "type": "string",
                            "description": "Repository URL (for clone)",
                        },
                        "path": {
                            "type": "string",
                            "description": "Local path",
                        },
                        "message": {
                            "type": "string",
                            "description": "Commit message",
                        },
                        "branch": {
                            "type": "string",
                            "description": "Branch name",
                        },
                    },
                    "required": ["operation"],
                },
                sandboxed=True,
                permissions=["git"],
            )
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation")

        try:
            if operation == "clone":
                repo_url = kwargs.get("repo_url")
                path = kwargs.get("path", ".")
                
                result = subprocess.run(
                    ["git", "clone", repo_url, path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.returncode != 0 else None,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "commit":
                message = kwargs.get("message", "Update")
                
                subprocess.run(["git", "add", "-A"], check=True)
                result = subprocess.run(
                    ["git", "commit", "-m", message],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.returncode != 0 else None,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "push":
                branch = kwargs.get("branch", "main")
                result = subprocess.run(
                    ["git", "push", "origin", branch],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.returncode != 0 else None,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "pull":
                branch = kwargs.get("branch", "main")
                result = subprocess.run(
                    ["git", "pull", "origin", branch],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.returncode != 0 else None,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "branch":
                result = subprocess.run(
                    ["git", "branch", "-a"],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout.split("\n"),
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "status":
                result = subprocess.run(
                    ["git", "status"],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "log":
                result = subprocess.run(
                    ["git", "log", "--oneline", "-20"],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout.split("\n"),
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "diff":
                result = subprocess.run(
                    ["git", "diff"],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "checkout":
                branch = kwargs.get("branch")
                result = subprocess.run(
                    ["git", "checkout", branch],
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.returncode != 0 else None,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            elif operation == "add":
                files = kwargs.get("files", ["-A"])
                result = subprocess.run(
                    ["git", "add"] + files,
                    capture_output=True,
                    text=True,
                )
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    tool_name=self.name,
                    parameters=kwargs,
                )

            return ToolResult(
                success=False,
                error=f"Unknown operation: {operation}",
                tool_name=self.name,
                parameters=kwargs,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=self.name,
                parameters=kwargs,
            )


class PythonTool(Tool):
    """Tool for executing Python code."""

    def __init__(self):
        super().__init__(
            ToolConfig(
                name="python",
                description="Execute Python code in a sandboxed environment",
                category=ToolCategory.EXECUTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        },
                        "globals": {
                            "type": "object",
                            "description": "Global variables to pass",
                        },
                        "locals": {
                            "type": "object",
                            "description": "Local variables to pass",
                        },
                    },
                    "required": ["code"],
                },
                sandboxed=True,
                permissions=["exec"],
                timeout=120,
            )
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code")
        globals_dict = kwargs.get("globals", {})
        locals_dict = kwargs.get("locals", {})

        try:
            import io
            from contextlib import redirect_stdout, redirect_stderr

            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec_result = exec(code, globals_dict, locals_dict)

            return ToolResult(
                success=True,
                output={
                    "stdout": stdout_capture.getvalue(),
                    "stderr": stderr_capture.getvalue(),
                    "result": str(exec_result) if exec_result is not None else None,
                },
                tool_name=self.name,
                parameters=kwargs,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Python execution error: {str(e)}",
                tool_name=self.name,
                parameters=kwargs,
            )


class TerminalTool(Tool):
    """Tool for executing terminal commands."""

    def __init__(self):
        super().__init__(
            ToolConfig(
                name="terminal",
                description="Execute shell commands",
                category=ToolCategory.EXECUTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Command to execute",
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory",
                        },
                        "env": {
                            "type": "object",
                            "description": "Environment variables",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds",
                        },
                    },
                    "required": ["command"],
                },
                sandboxed=True,
                permissions=["exec"],
                timeout=300,
            )
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        command = kwargs.get("command")
        cwd = kwargs.get("cwd")
        env = kwargs.get("env")
        timeout = kwargs.get("timeout", 60)

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env={**os.environ, **(env or {})},
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return ToolResult(
                success=result.returncode == 0,
                output={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
                error=None if result.returncode == 0 else result.stderr,
                tool_name=self.name,
                parameters=kwargs,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error=f"Command timed out after {timeout}s",
                tool_name=self.name,
                parameters=kwargs,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=self.name,
                parameters=kwargs,
            )


class SearchTool(Tool):
    """Tool for web search."""

    def __init__(self):
        super().__init__(
            ToolConfig(
                name="search",
                description="Search the web for information",
                category=ToolCategory.NETWORK,
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                        },
                    },
                    "required": ["query"],
                },
                sandboxed=False,
                permissions=["network"],
            )
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query")
        num_results = kwargs.get("num_results", 5)

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": "1",
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

            return ToolResult(
                success=True,
                output={
                    "query": query,
                    "results": data.get("RelatedTopics", [])[:num_results],
                    "abstract": data.get("AbstractText", ""),
                    "source": data.get("Heading", ""),
                },
                tool_name=self.name,
                parameters=kwargs,
            )

        except ImportError:
            return ToolResult(
                success=False,
                error="httpx not installed. Install with: pip install httpx",
                tool_name=self.name,
                parameters=kwargs,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=self.name,
                parameters=kwargs,
            )
