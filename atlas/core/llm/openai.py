"""OpenAI LLM client implementation."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Optional
import time

from atlas.core.llm.base import BaseLLM, Message, ChatResponse, StreamChunk, MessageRole


class OpenAIClient(BaseLLM):
    """OpenAI API client."""

    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            timeout=timeout,
            max_retries=max_retries,
        )

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
        """Send a chat completion request to OpenAI."""
        import httpx

        formatted_messages = self._format_messages(messages)

        request_data = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
        }

        if max_tokens:
            request_data["max_tokens"] = max_tokens
        if stop:
            request_data["stop"] = stop
        if tools:
            request_data["tools"] = tools
            if tool_choice:
                request_data["tool_choice"] = tool_choice

        request_data.update(kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=request_data,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
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

        choice = data.get("choices", [{}])[0]
        message_data = choice.get("message", {})

        self._total_tokens += data.get("usage", {}).get("total_tokens", 0)
        self._request_count += 1

        return ChatResponse(
            content=message_data.get("content", ""),
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            tool_calls=message_data.get("tool_calls"),
            id=data.get("id"),
            created=data.get("created", int(time.time())),
        )

    async def stream(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion response from OpenAI."""
        import httpx

        formatted_messages = self._format_messages(messages)

        request_data = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens:
            request_data["max_tokens"] = max_tokens
        if tools:
            request_data["tools"] = tools

        request_data.update(kwargs)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break

                        import json
                        data = json.loads(data_str)

                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})

                        yield StreamChunk(
                            content=delta.get("content", ""),
                            delta=delta.get("content", ""),
                            finish_reason=choice.get("finish_reason"),
                            tool_calls=delta.get("tool_calls"),
                        )

    def _format_messages(
        self,
        messages: list[Message | dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format messages for OpenAI API."""
        formatted = []

        for msg in messages:
            if isinstance(msg, dict):
                formatted.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
            else:
                msg_dict = {"role": msg.role.value, "content": msg.content}

                if msg.name:
                    msg_dict["name"] = msg.name
                if msg.tool_calls:
                    msg_dict["tool_calls"] = msg.tool_calls
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id

                formatted.append(msg_dict)

        return formatted


class AzureOpenAIClient(BaseLLM):
    """Azure OpenAI API client."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_version: str = "2024-02-01",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=azure_endpoint,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.api_version = api_version

    async def chat(
        self,
        messages: list[Message | dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat completion request to Azure OpenAI."""
        import httpx

        formatted_messages = self._format_messages(messages)

        request_data = {
            "messages": formatted_messages,
            **kwargs,
        }

        if tools:
            request_data["tools"] = tools

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["api-key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.base_url}/openai/deployments/{self.model}/chat/completions",
                        json=request_data,
                        headers=headers,
                        params={"api-version": self.api_version},
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

        choice = data.get("choices", [{}])[0]
        message_data = choice.get("message", {})

        self._total_tokens += data.get("usage", {}).get("total_tokens", 0)
        self._request_count += 1

        return ChatResponse(
            content=message_data.get("content", ""),
            model=self.model,
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            tool_calls=message_data.get("tool_calls"),
        )

    async def stream(
        self,
        messages: list[Message | dict[str, Any]],
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a chat completion response from Azure OpenAI."""
        import httpx

        formatted_messages = self._format_messages(messages)

        request_data = {
            "messages": formatted_messages,
            "stream": True,
            **kwargs,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/openai/deployments/{self.model}/chat/completions",
                json=request_data,
                headers=headers,
                params={"api-version": self.api_version},
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break

                        import json
                        data = json.loads(data_str)

                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})

                        yield StreamChunk(
                            content=delta.get("content", ""),
                            delta=delta.get("content", ""),
                            finish_reason=choice.get("finish_reason"),
                        )

    def _format_messages(
        self,
        messages: list[Message | dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Format messages for Azure OpenAI API."""
        formatted = []

        for msg in messages:
            if isinstance(msg, dict):
                formatted.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
            else:
                msg_dict = {"role": msg.role.value, "content": msg.content}
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                formatted.append(msg_dict)

        return formatted
