"""Agent management API routes."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from atlas.core.agents.base import AgentConfig, AgentType


router = APIRouter()


class CreateAgentRequest(BaseModel):
    """Request to create a new agent."""
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=200)
    goal: str = Field(..., min_length=1)
    agent_type: str = Field(default="custom")
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    max_iterations: int = Field(default=100, ge=1, le=1000)
    max_tokens: int = Field(default=128000, ge=1000)
    timeout_seconds: int = Field(default=3600, ge=1)
    budget: float = Field(default=100.0, ge=0)
    temperature: float = Field(default=0.7, ge=0, le=2)
    model: str | None = None


class AgentResponse(BaseModel):
    """Agent response model."""
    id: str
    name: str
    role: str
    status: str
    agent_type: str
    message_count: int = 0
    metrics: dict[str, Any] = {}


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent."""
    agent_id: str
    input: str = Field(..., min_length=1)
    stream: bool = Field(default=False)


class AgentExecuteResponse(BaseModel):
    """Response from agent execution."""
    agent_id: str
    status: str
    result: str
    metrics: dict[str, Any] = {}


@router.get("/", response_model=list[AgentResponse])
async def list_agents() -> list[dict[str, Any]]:
    """List all registered agents."""
    return []


@router.post("/", response_model=AgentResponse)
async def create_agent(request: CreateAgentRequest) -> dict[str, Any]:
    """Create a new agent."""
    agent_id = str(uuid4())
    
    return {
        "id": agent_id,
        "name": request.name,
        "role": request.role,
        "status": "idle",
        "agent_type": request.agent_type,
        "message_count": 0,
        "metrics": {
            "iterations": 0,
            "tokens_used": 0,
            "cost": 0.0,
            "tool_calls": 0,
            "errors": 0,
        },
    }


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str) -> dict[str, Any]:
    """Get agent details."""
    return {
        "id": agent_id,
        "name": "Sample Agent",
        "role": "assistant",
        "status": "idle",
        "agent_type": "custom",
        "message_count": 0,
        "metrics": {},
    }


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str) -> dict[str, str]:
    """Delete an agent."""
    return {"status": "deleted", "agent_id": agent_id}


@router.post("/{agent_id}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
) -> dict[str, Any]:
    """Execute an agent with input."""
    return {
        "agent_id": agent_id,
        "status": "completed",
        "result": "Agent execution result",
        "metrics": {
            "iterations": 1,
            "tokens_used": 100,
            "cost": 0.01,
        },
    }


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str) -> dict[str, str]:
    """Stop a running agent."""
    return {"status": "stopped", "agent_id": agent_id}


@router.get("/{agent_id}/messages")
async def get_agent_messages(agent_id: str) -> list[dict[str, Any]]:
    """Get agent message history."""
    return []


@router.delete("/{agent_id}/messages")
async def clear_agent_messages(agent_id: str) -> dict[str, str]:
    """Clear agent message history."""
    return {"status": "cleared", "agent_id": agent_id}
