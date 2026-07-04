"""HTTP client tool."""

from __future__ import annotations

from typing import Any, Optional

from atlas.core.tools.base import BaseTool, ToolParameter, ToolResult


class HttpTool(BaseTool):
    """Tool for making HTTP requests."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        default_headers: Optional[dict] = None,
    ):
        super().__init__(
            name="http",
            description="Make HTTP requests",
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = default_headers or {}
        self.register_parameters()

    def register_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="method",
            type="string",
            description="HTTP method",
            required=True,
            enum=["GET", "POST", "PUT", "DELETE", "PATCH"],
        ))
        self.add_parameter(ToolParameter(
            name="url",
            type="string",
            description="URL to request",
            required=True,
        ))
        self.add_parameter(ToolParameter(
            name="headers",
            type="object",
            description="HTTP headers",
            required=False,
        ))
        self.add_parameter(ToolParameter(
            name="body",
            type="string",
            description="Request body",
            required=False,
        ))

    async def execute(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        body: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute an HTTP request."""
        import aiohttp
        
        all_headers = {**self.default_headers, **(headers or {})}
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=all_headers,
                        json=body if body else None,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        content = await response.text()
                        return ToolResult(
                            success=response.status < 400,
                            data={
                                "status": response.status,
                                "headers": dict(response.headers),
                                "body": content,
                            },
                        )
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    return ToolResult(success=False, error=str(e))
            except Exception as e:
                return ToolResult(success=False, error=str(e))
        
        return ToolResult(success=False, error="Max retries exceeded")