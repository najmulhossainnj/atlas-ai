"""Anthropic LLM client implementation."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Optional
import time

from atlas.core.llm.base import BaseLLM, Message, ChatResponse, StreamChunk, MessageRole


class AnthropicClient(BaseLLM):
    """Anthropic Claude API client."""

    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(
        self,
        model: str = "claude-3-opus-20240229",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url or self.BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
        )

    async def chat(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat completion request to Anthropic."""
        import httpx

        formatted_messages = self._format_messages(messages)

        request_data = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system:
            request_data["system"] = system

        if tools:
            request_data["tools"] = self._format_tools(tools)
            if tool_choice:
                request_data["tool_choice"] = {"type": "tool", "name": tool_choice}

        request_data.update(kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.base_url}/messages",
                        json=request_data,
                        headers={
                            "x-api-key": self.api_key or "",
                            "Content-Type": "application/json",
                            "anthropic-version": "2023-06-01",
                        },
                    )

                    if response.status_code == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue

                    response.raise_for_status()
                    data = response.json()
                    break
                except httpx.HTTPStatusError as e:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise e

        content = data.get("content", [])
        response_text = ""
        tool_uses = None

        for block in content:
            if block.get("type") == "text":
                response_text = block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_uses = [block]

        usage = data.get("usage", {})

        self._total_tokens += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        self._request_count += 1

        return ChatResponse(
            content=response_text,
            model=self.model,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
            finish_reason=data.get("stop_reason"),
            tool_calls=tool_uses,
            created=int(time.time()),
        )

    async def stream(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion response from Anthropic."""
        import httpx

        formatted_messages = self._format_messages(messages)

        request_data = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if system:
            request_data["system"] = system

        if tools:
            request_data["tools"] = self._format_tools(tools)

        request_data.update(kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                json=request_data,
                headers={
                    "x-api-key": self.api_key or "",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "":
                            continue

                        import json
                        data = json.loads(data_str)

                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            yield StreamChunk(
                                content=delta.get("text", ""),
                                delta=delta.get("text", ""),
                            )
                        elif data.get("type") == "message_delta":
                            yield StreamChunk(
                                content="",
                                finish_reason=data.get("content_block", {}).get("type"),
                            )

    def _format_messages(
        self,
        messages: list[Message | dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format messages for Anthropic API."""
        formatted = []

        for msg in messages:
            role = msg.get("role") if isinstance(msg, dict) else msg.role.value

            if role == "system":
                continue

            if isinstance(msg, dict):
                formatted.append({
                    "role": "user" if role == "user" else "assistant",
                    "content": msg.get("content", ""),
                })
            else:
                formatted.append({
                    "role": "user" if msg.role == MessageRole.USER else "assistant",
                    "content": msg.content,
                })

        return formatted

    def _format_tools(
        self,
        tools: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format tools for Anthropic API."""
        formatted_tools = []

        for tool in tools:
            formatted_tool = {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "input_schema": tool.get("parameters", {}),
            }
            formatted_tools.append(formatted_tool)

        return formatted_tools
