"""Filesystem tool for file operations."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from atlas.core.tools.base import BaseTool, ToolParameter, ToolResult


class FilesystemTool(BaseTool):
    """Tool for filesystem operations."""

    def __init__(self, base_path: str = "."):
        super().__init__(
            name="filesystem",
            description="Perform filesystem operations",
        )
        self.base_path = Path(base_path).resolve()
        self.register_parameters()

    def register_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="operation",
            type="string",
            description="Operation to perform",
            required=True,
            enum=["read", "write", "list", "exists", "delete", "mkdir", "copy", "move"],
        ))
        self.add_parameter(ToolParameter(
            name="path",
            type="string",
            description="File or directory path",
            required=True,
        ))
        self.add_parameter(ToolParameter(
            name="content",
            type="string",
            description="Content to write (for write operation)",
            required=False,
        ))

    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base path."""
        resolved = (self.base_path / path).resolve()
        if not str(resolved).startswith(str(self.base_path)):
            raise ValueError("Path is outside base directory")
        return resolved

    async def execute(
        self,
        operation: str,
        path: str,
        content: str = None,
        **kwargs,
    ) -> ToolResult:
        """Execute filesystem operation."""
        try:
            resolved_path = self._resolve_path(path)

            if operation == "read":
                return await self._read(resolved_path)
            elif operation == "write":
                return await self._write(resolved_path, content or "")
            elif operation == "list":
                return await self._list_dir(resolved_path)
            elif operation == "exists":
                return await self._exists(resolved_path)
            elif operation == "delete":
                return await self._delete(resolved_path)
            elif operation == "mkdir":
                return await self._mkdir(resolved_path)
            elif operation == "copy":
                dest = kwargs.get("destination", "")
                return await self._copy(resolved_path, self._resolve_path(dest))
            elif operation == "move":
                dest = kwargs.get("destination", "")
                return await self._move(resolved_path, self._resolve_path(dest))
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _read(self, path: Path) -> ToolResult:
        if not path.exists():
            return ToolResult(success=False, error="File not found")
        if not path.is_file():
            return ToolResult(success=False, error="Path is not a file")

        content = path.read_text()
        return ToolResult(success=True, data={"content": content, "size": len(content)})

    async def _write(self, path: Path, content: str) -> ToolResult:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return ToolResult(success=True, data={"path": str(path), "size": len(content)})

    async def _list_dir(self, path: Path) -> ToolResult:
        if not path.exists():
            return ToolResult(success=False, error="Directory not found")
        if not path.is_dir():
            return ToolResult(success=False, error="Path is not a directory")

        entries = []
        for entry in path.iterdir():
            entries.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else 0,
            })
        return ToolResult(success=True, data={"entries": entries, "count": len(entries)})

    async def _exists(self, path: Path) -> ToolResult:
        return ToolResult(success=True, data={"exists": path.exists(), "is_file": path.is_file(), "is_dir": path.is_dir()})

    async def _delete(self, path: Path) -> ToolResult:
        if not path.exists():
            return ToolResult(success=False, error="Path not found")
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        return ToolResult(success=True, data={"deleted": str(path)})

    async def _mkdir(self, path: Path) -> ToolResult:
        path.mkdir(parents=True, exist_ok=True)
        return ToolResult(success=True, data={"created": str(path)})

    async def _copy(self, src: Path, dest: Path) -> ToolResult:
        if src.is_file():
            shutil.copy2(src, dest)
        else:
            shutil.copytree(src, dest)
        return ToolResult(success=True, data={"copied": str(src), "to": str(dest)})

    async def _move(self, src: Path, dest: Path) -> ToolResult:
        shutil.move(str(src), str(dest))
        return ToolResult(success=True, data={"moved": str(src), "to": str(dest)})