"""Main FastAPI application."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import structlog

from atlas.backend.api.routes import agents, memory, tools, workflows, llm, execution
from atlas.core.agents.orchestrator import AgentOrchestrator
from atlas.core.memory.manager import MemoryManager
from atlas.core.tools.registry import ToolRegistry, get_tool_registry
from atlas.core.workflow.executor import WorkflowExecutor
from atlas.core.llm.factory import LLMFactory, LLMConfig


logger = structlog.get_logger()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    agents_registered: int
    workflows_active: int


app_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    logger.info("Starting Atlas API server")

    orchestrator = AgentOrchestrator()
    memory_manager = MemoryManager()
    tool_registry = await get_tool_registry()
    workflow_executor = WorkflowExecutor()

    app_state["orchestrator"] = orchestrator
    app_state["memory_manager"] = memory_manager
    app_state["tool_registry"] = tool_registry
    app_state["workflow_executor"] = workflow_executor

    LLMFactory.set_default_config(LLMConfig())

    yield

    logger.info("Shutting down Atlas API server")


app = FastAPI(
    title="Atlas API",
    description="A Modular Agentic AI Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(execution.router, prefix="/api/v1/execution", tags=["execution"])


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    orchestrator = app_state.get("orchestrator")
    workflow_executor = app_state.get("workflow_executor")

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        agents_registered=len(orchestrator.registry.agents) if orchestrator else 0,
        workflows_active=len(workflow_executor.list_executions()) if workflow_executor else 0,
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif message_type == "execute":
                result = await handle_execution(data)
                await websocket.send_json({"type": "result", "data": result})
            elif message_type == "stream":
                await handle_streaming(websocket, data)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        await websocket.send_json({"type": "error", "error": str(e)})


async def handle_execution(data: dict[str, Any]) -> dict[str, Any]:
    """Handle execution requests."""
    return {"status": "completed", "result": {}}


async def handle_streaming(websocket: WebSocket, data: dict[str, Any]) -> None:
    """Handle streaming requests."""
    await websocket.send_json({"type": "stream_start"})
    await asyncio.sleep(0.1)
    await websocket.send_json({"type": "stream_data", "data": "processing..."})
    await asyncio.sleep(0.1)
    await websocket.send_json({"type": "stream_end"})


@app.get("/api/v1/status")
async def get_status() -> dict[str, Any]:
    """Get overall system status."""
    orchestrator = app_state.get("orchestrator")
    memory_manager = app_state.get("memory_manager")
    tool_registry = app_state.get("tool_registry")
    workflow_executor = app_state.get("workflow_executor")

    return {
        "orchestrator": await orchestrator.get_status() if orchestrator else {},
        "memory": await memory_manager.get_stats() if memory_manager else {},
        "tools": {
            "total": len(await tool_registry.list_tools()) if tool_registry else 0,
            "categories": await tool_registry.list_categories() if tool_registry else [],
        },
        "workflows": {
            "active": len(workflow_executor.list_executions()) if workflow_executor else 0,
        },
    }
