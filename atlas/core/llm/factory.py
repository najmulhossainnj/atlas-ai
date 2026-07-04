"""LLM factory for creating and managing LLM clients."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from atlas.core.llm.base import BaseLLM, Message, ChatResponse, StreamChunk
from atlas.core.llm.openai import OpenAIClient
from atlas.core.llm.anthropic import AnthropicClient


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AZURE = "azure"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """Configuration for LLM clients."""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    streaming: bool = True
    tools_enabled: bool = True
    reasoning_enabled: bool = False
    fallback_models: list[str] = field(default_factory=list)
    cost_per_token: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMFactory:
    """Factory for creating LLM clients."""

    _providers: dict[str, type[BaseLLM]] = {}
    _clients: dict[str, BaseLLM] = {}
    _default_config: Optional[LLMConfig] = None

    @classmethod
    def register_provider(cls, name: str, provider_class: type[BaseLLM]) -> None:
        """Register a new LLM provider."""
        cls._providers[name] = provider_class

    @classmethod
    def create(
        cls,
        config: Optional[LLMConfig] = None,
        name: str = "default",
    ) -> BaseLLM:
        """Create an LLM client based on configuration."""
        if config is None:
            config = cls._default_config or LLMConfig()

        config.api_key = config.api_key or os.environ.get(
            f"{config.provider.name.upper()}_API_KEY"
        )

        provider_class = cls._providers.get(config.provider.value)
        if not provider_class:
            if config.provider == LLMProvider.OPENAI:
                provider_class = OpenAIClient
            elif config.provider == LLMProvider.ANTHROPIC:
                provider_class = AnthropicClient
            elif config.provider == LLMProvider.OLLAMA:
                provider_class = OllamaClient
            else:
                raise ValueError(f"Unknown provider: {config.provider}")

        client = provider_class(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

        cls._clients[name] = client
        return client

    @classmethod
    def get(cls, name: str = "default") -> Optional[BaseLLM]:
        """Get a registered LLM client."""
        return cls._clients.get(name)

    @classmethod
    def set_default_config(cls, config: LLMConfig) -> None:
        """Set the default configuration for new clients."""
        cls._default_config = config

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers."""
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered clients."""
        cls._clients.clear()


class LLMRouter:
    """Routes requests to appropriate LLM providers."""

    def __init__(self):
        self._routes: dict[str, LLMConfig] = {}
        self._primary: Optional[LLMClient] = None
        self._fallbacks: list[LLMClient] = []

    def add_route(
        self,
        route_key: str,
        config: LLMConfig,
    ) -> None:
        """Add a routing rule."""
        self._routes[route_key] = config

    def set_primary(self, config: LLMConfig) -> None:
        """Set the primary LLM client."""
        self._primary = LLMClient(config)

    def add_fallback(self, config: LLMConfig) -> None:
        """Add a fallback LLM client."""
        self._fallbacks.append(LLMClient(config))

    async def chat(
        self,
        messages: list[Message | dict[str, Any]],
        route_key: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Route and execute a chat request."""
        if route_key and route_key in self._routes:
            config = self._routes[route_key]
            client = LLMClient(config)
            return await client.chat(messages, **kwargs)

        if self._primary:
            try:
                return await self._primary.chat(messages, **kwargs)
            except Exception as e:
                for fallback in self._fallbacks:
                    try:
                        return await fallback.chat(messages, **kwargs)
                    except Exception:
                        continue
                raise e

        raise ValueError("No LLM client configured")


class LLMClient:
    """Wrapper for LLM clients with additional functionality."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = LLMFactory.create(config)
        self._usage_log: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat request with tracking."""
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        response = await self.client.chat(
            messages=messages,
            tools=tools if self.config.tools_enabled else None,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        self._usage_log.append({
            "timestamp": response.created,
            "model": response.model,
            "usage": response.usage,
        })

        return response

    async def stream(
        self,
        messages: list[Message | dict[str, Any]],
        **kwargs: Any,
    ):
        """Stream a chat response."""
        temperature = kwargs.get("temperature") or self.config.temperature
        max_tokens = kwargs.get("max_tokens") or self.config.max_tokens

        return self.client.stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def get_usage_summary(self) -> dict[str, Any]:
        """Get a summary of token usage."""
        total_tokens = 0
        total_cost = 0.0

        for entry in self._usage_log:
            usage = entry.get("usage", {})
            tokens = usage.get("total_tokens", 0)
            total_tokens += tokens
            total_cost += tokens * self.config.cost_per_token

        return {
            "total_requests": len(self._usage_log),
            "total_tokens": total_tokens,
            "estimated_cost": total_cost,
        }


class OllamaClient(BaseLLM):
    """Ollama LLM client for local models."""

    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
        **kwargs: Any,
    ):
        super().__init__(model=model, **kwargs)
        self.base_url = base_url

    async def chat(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat request to Ollama."""
        import httpx

        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "stream": False,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()

        return ChatResponse(
            content=data.get("message", {}).get("content", ""),
            model=self.model,
            usage={
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        )

    async def stream(
        self,
        messages: list[Message | dict[str, Any]],
        **kwargs: Any,
    ):
        """Stream a chat response from Ollama."""
        import httpx
        from atlas.core.llm.base import StreamChunk

        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "stream": True,
                    **kwargs,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json as json_module
                        data = json_module.loads(line)
                        yield StreamChunk(
                            content=data.get("message", {}).get("content", ""),
                            delta=data.get("message", {}).get("content", ""),
                        )


LLMFactory.register_provider("ollama", OllamaClient)
