"""Atlas - A Modular Agentic AI Platform."""

__version__ = "0.1.0"
__author__ = "Atlas Team"

from atlas.core.agents.base import Agent, AgentConfig
from atlas.core.agents.orchestrator import AgentOrchestrator
from atlas.core.memory.manager import MemoryManager
from atlas.core.tools.registry import ToolRegistry
from atlas.core.planning.engine import PlanningEngine
from atlas.core.workflow.executor import WorkflowExecutor
from atlas.core.llm.factory import LLMFactory

__all__ = [
    "__version__",
    "Agent",
    "AgentConfig",
    "AgentOrchestrator",
    "MemoryManager",
    "ToolRegistry",
    "PlanningEngine",
    "WorkflowExecutor",
    "LLMFactory",
]
