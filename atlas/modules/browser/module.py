"""Browser automation module using Playwright."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass, field
from typing import Any, Optional
import json


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    timeout: int = 30000
    screenshot_format: str = "png"


@dataclass
class BrowserAction:
    """A browser action to be executed."""
    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserResult:
    """Result of a browser action."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    screenshot: Optional[str] = None


class BrowserModule:
    """Module for browser automation tasks."""

    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._context = None
        self._page = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the browser."""
        if self._initialized:
            return

        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.config.headless
            )
            self._context = await self._browser.new_context(
                viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
                user_agent=self.config.user_agent,
            )
            self._page = await self._context.new_page()
            self._initialized = True
        except ImportError:
            raise ImportError("Playwright is not installed. Install with: pip install playwright && playwright install chromium")

    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._initialized = False

    async def navigate(self, url: str) -> BrowserResult:
        """Navigate to a URL."""
        await self._ensure_initialized()
        
        try:
            response = await self._page.goto(url, timeout=self.config.timeout)
            return BrowserResult(
                success=True,
                data={
                    "url": self._page.url,
                    "title": await self._page.title(),
                    "status": response.status if response else None,
                }
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def click(self, selector: str) -> BrowserResult:
        """Click an element."""
        await self._ensure_initialized()
        
        try:
            await self._page.click(selector, timeout=self.config.timeout)
            return BrowserResult(success=True, data={"selector": selector})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def fill(self, selector: str, value: str) -> BrowserResult:
        """Fill an input field."""
        await self._ensure_initialized()
        
        try:
            await self._page.fill(selector, value)
            return BrowserResult(success=True, data={"selector": selector, "value": value})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def type_text(self, selector: str, text: str, delay: int = 0) -> BrowserResult:
        """Type text into an element."""
        await self._ensure_initialized()
        
        try:
            await self._page.type(selector, text, delay=delay)
            return BrowserResult(success=True, data={"selector": selector, "text": text})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_text(self, selector: str) -> BrowserResult:
        """Get text content of an element."""
        await self._ensure_initialized()
        
        try:
            text = await self._page.text_content(selector)
            return BrowserResult(success=True, data={"selector": selector, "text": text})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_attribute(self, selector: str, attribute: str) -> BrowserResult:
        """Get an attribute of an element."""
        await self._ensure_initialized()
        
        try:
            value = await self._page.get_attribute(selector, attribute)
            return BrowserResult(success=True, data={"selector": selector, "attribute": attribute, "value": value})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def screenshot(self, path: Optional[str] = None) -> BrowserResult:
        """Take a screenshot."""
        await self._ensure_initialized()
        
        try:
            if path:
                await self._page.screenshot(path=path, full_page=True)
                return BrowserResult(success=True, data={"path": path})
            else:
                screenshot_bytes = await self._page.screenshot(full_page=True)
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
                return BrowserResult(success=True, data={"screenshot": screenshot_base64}, screenshot=screenshot_base64)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def execute_script(self, script: str) -> BrowserResult:
        """Execute JavaScript."""
        await self._ensure_initialized()
        
        try:
            result = await self._page.evaluate(script)
            return BrowserResult(success=True, data=result)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> BrowserResult:
        """Wait for a selector to appear."""
        await self._ensure_initialized()
        
        try:
            await self._page.wait_for_selector(selector, timeout=timeout or self.config.timeout)
            return BrowserResult(success=True, data={"selector": selector})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def select_option(self, selector: str, value: str) -> BrowserResult:
        """Select an option from a dropdown."""
        await self._ensure_initialized()
        
        try:
            await self._page.select_option(selector, value)
            return BrowserResult(success=True, data={"selector": selector, "value": value})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def check(self, selector: str) -> BrowserResult:
        """Check a checkbox or radio button."""
        await self._ensure_initialized()
        
        try:
            await self._page.check(selector)
            return BrowserResult(success=True, data={"selector": selector})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def hover(self, selector: str) -> BrowserResult:
        """Hover over an element."""
        await self._ensure_initialized()
        
        try:
            await self._page.hover(selector)
            return BrowserResult(success=True, data={"selector": selector})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_page_info(self) -> BrowserResult:
        """Get information about the current page."""
        await self._ensure_initialized()
        
        try:
            return BrowserResult(success=True, data={
                "url": self._page.url,
                "title": await self._page.title(),
                "viewport_size": self._page.viewport_size,
            })
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def download_file(self, url: str, path: str) -> BrowserResult:
        """Download a file."""
        await self._ensure_initialized()
        
        try:
            async with self._page.request.get(url) as response:
                content = await response.body()
                with open(path, "wb") as f:
                    f.write(content)
            return BrowserResult(success=True, data={"path": path})
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def _ensure_initialized(self) -> None:
        """Ensure browser is initialized."""
        if not self._initialized:
            await self.initialize()
