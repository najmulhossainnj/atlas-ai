"""LLM management API routes."""

from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter()


class MessageRequest(BaseModel):
    """Chat message."""
    role: str = Field(default="user")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    """Chat completion request."""
    messages: list[MessageRequest]
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Chat completion response."""
    id: str
    model: str
    content: str
    usage: dict[str, int] = {}
    finish_reason: Optional[str] = None


class EmbeddingRequest(BaseModel):
    """Embedding request."""
    text: str = Field(..., min_length=1)
    model: Optional[str] = None


class EmbeddingResponse(BaseModel):
    """Embedding response."""
    embedding: list[float]
    model: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict[str, Any]:
    """Send a chat completion request."""
    return {
        "id": str(uuid4()),
        "model": request.model or "gpt-4",
        "content": "Response from LLM",
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 30,
            "total_tokens": 80,
        },
        "finish_reason": "stop",
    }


@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest) -> dict[str, Any]:
    """Create text embeddings."""
    return {
        "embedding": [0.1] * 384,
        "model": request.model or "text-embedding-ada-002",
    }


@router.get("/models")
async def list_models() -> dict[str, Any]:
    """List available models."""
    return {
        "models": [
            {"id": "gpt-4", "provider": "openai", "context_length": 128000},
            {"id": "gpt-4-turbo", "provider": "openai", "context_length": 128000},
            {"id": "gpt-3.5-turbo", "provider": "openai", "context_length": 16385},
            {"id": "claude-3-opus", "provider": "anthropic", "context_length": 200000},
            {"id": "claude-3-sonnet", "provider": "anthropic", "context_length": 200000},
            {"id": "llama2", "provider": "ollama", "context_length": 4096},
        ]
    }


@router.get("/providers")
async def list_providers() -> list[dict[str, Any]]:
    """List available LLM providers."""
    return [
        {"id": "openai", "name": "OpenAI", "models": ["gpt-4", "gpt-3.5-turbo"]},
        {"id": "anthropic", "name": "Anthropic", "models": ["claude-3-opus", "claude-3-sonnet"]},
        {"id": "ollama", "name": "Ollama", "models": ["llama2", "mistral"]},
    ]


@router.get("/stats")
async def get_llm_stats() -> dict[str, Any]:
    """Get LLM usage statistics."""
    return {
        "total_requests": 1000,
        "total_tokens": 500000,
        "estimated_cost": 10.50,
        "by_model": {
            "gpt-4": {"requests": 600, "tokens": 300000, "cost": 6.00},
            "claude-3-opus": {"requests": 400, "tokens": 200000, "cost": 4.50},
        },
    }
