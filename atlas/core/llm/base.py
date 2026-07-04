"""Base LLM classes and interfaces."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional
import time


class MessageRole(str, Enum):
    """Message roles for LLM interactions."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A message in an LLM conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ChatResponse:
    """Response from an LLM chat completion."""
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    id: Optional[str] = None
    created: int = field(default_factory=lambda: int(time.time()))


@dataclass
class StreamChunk:
    """A chunk in a streaming response."""
    content: str
    delta: str = ""
    finish_reason: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None


class BaseLLM(ABC):
    """Base class for all LLM providers."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._total_tokens = 0
        self._total_cost = 0.0
        self._request_count = 0

    @abstractmethod
    async def chat(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat completion request."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion response."""
        pass

    def get_stats(self) -> dict[str, Any]:
        """Get usage statistics."""
        return {
            "model": self.model,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
            "request_count": self._request_count,
        }

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self._total_tokens = 0
        self._total_cost = 0.0
        self._request_count = 0


class RetryHandler:
    """Handles retries with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)

    async def execute_with_retry(
        self,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with retries."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise last_exception
