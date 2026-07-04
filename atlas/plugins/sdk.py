"""Plugin SDK for creating Atlas plugins."""

from __future__ import annotations

import asyncio
import importlib
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import json
import os


class PluginType(str, Enum):
    """Types of plugins."""
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    LLM = "llm"
    STORAGE = "storage"
    UI = "ui"
    CUSTOM = "custom"


@dataclass
class PluginConfig:
    """Configuration for a plugin."""
    name: str
    version: str = "0.1.0"
    description: str = ""
    plugin_type: PluginType = PluginType.CUSTOM
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class Plugin(ABC):
    """Base class for Atlas plugins."""

    def __init__(self, config: PluginConfig):
        self.config = config
        self._initialized = False
        self._enabled = True

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    async def enable(self) -> None:
        """Enable the plugin."""
        self._enabled = True

    async def disable(self) -> None:
        """Disable the plugin."""
        self._enabled = False

    def is_enabled(self) -> bool:
        """Check if the plugin is enabled."""
        return self._enabled

    def get_info(self) -> dict[str, Any]:
        """Get plugin information."""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "description": self.config.description,
            "type": self.config.plugin_type.value,
            "author": self.config.author,
            "enabled": self._enabled,
        }


class AgentPlugin(Plugin):
    """Base class for agent plugins."""

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.config.plugin_type = PluginType.AGENT

    @abstractmethod
    async def create_agent(self, **kwargs) -> Any:
        """Create an agent instance."""
        pass


class ToolPlugin(Plugin):
    """Base class for tool plugins."""

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.config.plugin_type = PluginType.TOOL

    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool."""
        pass

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Get the tool's parameter schema."""
        pass


class WorkflowPlugin(Plugin):
    """Base class for workflow plugins."""

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.config.plugin_type = PluginType.WORKFLOW

    @abstractmethod
    async def create_workflow(self, **kwargs) -> Any:
        """Create a workflow."""
        pass


class MemoryPlugin(Plugin):
    """Base class for memory plugins."""

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.config.plugin_type = PluginType.MEMORY

    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store a memory entry."""
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a memory entry."""
        pass

    @abstractmethod
    async def search(self, query: str, **kwargs) -> list[Any]:
        """Search memories."""
        pass


class LLMPlugin(Plugin):
    """Base class for LLM provider plugins."""

    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.config.plugin_type = PluginType.LLM

    @abstractmethod
    async def chat(self, messages: list[dict[str, Any]], **kwargs) -> dict[str, Any]:
        """Send a chat request."""
        pass

    @abstractmethod
    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings."""
        pass


class PluginManager:
    """Manages plugin loading and lifecycle."""

    def __init__(self, plugins_dir: Optional[str] = None):
        self._plugins: dict[str, Plugin] = {}
        self._plugins_dir = plugins_dir or "./plugins"
        self._lock = asyncio.Lock()

    async def load_plugin(self, plugin_class: type[Plugin], config: PluginConfig) -> Plugin:
        """Load and initialize a plugin."""
        async with self._lock:
            plugin = plugin_class(config)
            await plugin.initialize()
            self._plugins[config.name] = plugin
            return plugin

    async def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        async with self._lock:
            plugin = self._plugins.get(name)
            if plugin:
                await plugin.shutdown()
                del self._plugins[name]
                return True
            return False

    async def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    async def list_plugins(self, plugin_type: Optional[PluginType] = None) -> list[Plugin]:
        """List all plugins, optionally filtered by type."""
        plugins = list(self._plugins.values())
        if plugin_type:
            plugins = [p for p in plugins if p.config.plugin_type == plugin_type]
        return plugins

    async def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            await plugin.enable()
            return True
        return False

    async def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            await plugin.disable()
            return True
        return False

    async def load_from_directory(self) -> int:
        """Load plugins from the plugins directory."""
        if not os.path.exists(self._plugins_dir):
            return 0

        loaded = 0
        for filename in os.listdir(self._plugins_dir):
            if filename.endswith(".json"):
                plugin_path = os.path.join(self._plugins_dir, filename)
                try:
                    with open(plugin_path, "r") as f:
                        plugin_data = json.load(f)
                    
                    config = PluginConfig(
                        name=plugin_data.get("name", filename[:-5]),
                        version=plugin_data.get("version", "0.1.0"),
                        description=plugin_data.get("description", ""),
                        plugin_type=PluginType(plugin_data.get("type", "custom")),
                    )
                    
                    class_name = plugin_data.get("class")
                    module_path = plugin_data.get("module")
                    
                    if module_path and class_name:
                        module = importlib.import_module(module_path)
                        plugin_class = getattr(module, class_name)
                        
                        await self.load_plugin(plugin_class, config)
                        loaded += 1
                        
                except Exception:
                    pass

        return loaded

    async def shutdown_all(self) -> None:
        """Shutdown all plugins."""
        for plugin in self._plugins.values():
            await plugin.shutdown()
        self._plugins.clear()


def register_plugin(plugin_class: type[Plugin]) -> type[Plugin]:
    """Decorator to register a plugin class."""
    PluginRegistry._registry[plugin_class.__name__] = plugin_class
    return plugin_class


class PluginRegistry:
    """Registry for plugin classes."""
    _registry: dict[str, type[Plugin]] = {}


def create_example_agent_plugin() -> AgentPlugin:
    """Example of creating a custom agent plugin."""
    
    config = PluginConfig(
        name="example-agent",
        version="0.1.0",
        description="An example agent plugin",
        plugin_type=PluginType.AGENT,
    )

    class ExampleAgentPlugin(AgentPlugin):
        async def initialize(self) -> None:
            self._initialized = True

        async def shutdown(self) -> None:
            self._initialized = False

        async def create_agent(self, **kwargs):
            from atlas.core.agents.specialized import LLMAgent
            from atlas.core.agents.base import AgentConfig, AgentType
            
            return LLMAgent(
                AgentConfig(
                    name=kwargs.get("name", "Example Agent"),
                    role=kwargs.get("role", "Example"),
                    goal=kwargs.get("goal", ""),
                    agent_type=AgentType.CUSTOM,
                ),
                kwargs.get("llm_client"),
            )

    return ExampleAgentPlugin(config)


def create_example_tool_plugin() -> ToolPlugin:
    """Example of creating a custom tool plugin."""
    
    config = PluginConfig(
        name="example-tool",
        version="0.1.0",
        description="An example tool plugin",
        plugin_type=PluginType.TOOL,
    )

    class ExampleToolPlugin(ToolPlugin):
        async def initialize(self) -> None:
            self._initialized = True

        async def shutdown(self) -> None:
            self._initialized = False

        async def execute(self, **kwargs) -> dict[str, Any]:
            return {"success": True, "result": "Example tool executed"}

        def get_schema(self) -> dict[str, Any]:
            return {
                "name": "example-tool",
                "description": "An example tool",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            }

    return ExampleToolPlugin(config)
