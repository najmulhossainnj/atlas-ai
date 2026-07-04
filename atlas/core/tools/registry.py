"""Tool registry for managing available tools."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from atlas.core.tools.base import Tool, ToolConfig


class ToolRegistry:
    """Registry for managing and discovering tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._by_category: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the registry and load built-in tools."""
        if self._initialized:
            return

        await self._load_builtin_tools()
        self._initialized = True

    async def _load_builtin_tools(self) -> None:
        """Load built-in tools."""
        from atlas.core.tools.builtins import (
            FilesystemTool,
            GitTool,
            PythonTool,
            TerminalTool,
            SearchTool,
        )

        builtin_tools = [
            FilesystemTool(),
            GitTool(),
            PythonTool(),
            TerminalTool(),
            SearchTool(),
        ]

        for tool in builtin_tools:
            await self.register(tool)

    async def register(self, tool: Tool) -> None:
        """Register a new tool."""
        async with self._lock:
            self._tools[tool.name] = tool
            
            category = tool.config.category.value
            if category not in self._by_category:
                self._by_category[category] = []
            if tool.name not in self._by_category[category]:
                self._by_category[category].append(tool.name)

    async def unregister(self, tool_name: str) -> bool:
        """Unregister a tool."""
        async with self._lock:
            if tool_name not in self._tools:
                return False
            
            tool = self._tools.pop(tool_name)
            category = tool.config.category.value
            if category in self._by_category:
                self._by_category[category].remove(tool_name)
            
            return True

    async def get(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        async with self._lock:
            return self._tools.get(tool_name)

    async def list_tools(
        self,
        category: Optional[str] = None,
    ) -> list[Tool]:
        """List all tools, optionally filtered by category."""
        async with self._lock:
            if category:
                tool_names = self._by_category.get(category, [])
                return [self._tools[name] for name in tool_names if name in self._tools]
            return list(self._tools.values())

    async def list_categories(self) -> list[str]:
        """List all tool categories."""
        async with self._lock:
            return list(self._by_category.keys())

    async def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get schemas for all registered tools."""
        async with self._lock:
            return [tool.schema for tool in self._tools.values()]

    async def get_tool_stats(self) -> dict[str, Any]:
        """Get statistics for all tools."""
        async with self._lock:
            return {
                name: tool.get_stats()
                for name, tool in self._tools.items()
            }

    async def search(self, query: str) -> list[Tool]:
        """Search for tools by name or description."""
        async with self._lock:
            query_lower = query.lower()
            results = []
            
            for tool in self._tools.values():
                if (query_lower in tool.name.lower() or
                    query_lower in tool.description.lower()):
                    results.append(tool)
            
            return results


_global_registry: Optional[ToolRegistry] = None


async def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        await _global_registry.initialize()
    return _global_registry
