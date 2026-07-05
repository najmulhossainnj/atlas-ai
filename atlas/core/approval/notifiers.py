"""Notification system for approval requests."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ApprovalNotification:
    """A notification for an approval request."""
    request_id: str
    action: str
    description: str
    agent_name: str
    risk_level: str
    requested_at: str
    approval_url: Optional[str] = None


class Notifier(ABC):
    """Base notifier interface."""

    @abstractmethod
    async def send(self, notification: ApprovalNotification) -> bool:
        """Send a notification."""
        pass


class WebhookNotifier(Notifier):
    """Send notifications via webhook."""

    def __init__(self, webhook_url: str, headers: Optional[dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def send(self, notification: ApprovalNotification) -> bool:
        """Send notification via webhook."""
        import aiohttp
        
        payload = {
            "request_id": notification.request_id,
            "action": notification.action,
            "description": notification.description,
            "agent_name": notification.agent_name,
            "risk_level": notification.risk_level,
            "approval_url": notification.approval_url,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    return response.status < 400
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False


class SlackNotifier(Notifier):
    """Send notifications to Slack."""

    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel

    async def send(self, notification: ApprovalNotification) -> bool:
        """Send notification to Slack."""
        import aiohttp
        
        risk_emoji = {
            "low": ":large_blue_circle:",
            "medium": ":large_yellow_circle:",
            "high": ":large_orange_circle:",
            "critical": ":red_circle:",
        }
        
        emoji = risk_emoji.get(notification.risk_level, ":grey_question:")
        
        payload = {
            "channel": self.channel,
            "text": f"{emoji} Approval Required",
            "attachments": [{
                "color": "#ff9900",
                "title": notification.action,
                "text": notification.description,
                "fields": [
                    {"title": "Agent", "value": notification.agent_name, "short": True},
                    {"title": "Risk Level", "value": notification.risk_level, "short": True},
                ],
                "actions": [
                    {
                        "type": "button",
                        "text": "Approve",
                        "style": "primary",
                        "url": f"{notification.approval_url}?action=approve",
                    },
                    {
                        "type": "button",
                        "text": "Deny",
                        "style": "danger",
                        "url": f"{notification.approval_url}?action=deny",
                    },
                ],
            }],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status < 400
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False


class EmailNotifier(Notifier):
    """Send notifications via email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_emails: list[str],
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails

    async def send(self, notification: ApprovalNotification) -> bool:
        """Send notification via email."""
        try:
            import aiosmtplib
            
            message = f"""Subject: Approval Required - {notification.action}

Agent: {notification.agent_name}
Risk Level: {notification.risk_level}
Action: {notification.action}

Description:
{notification.description}

Request ID: {notification.request_id}

Approve: {notification.approval_url}?action=approve
Deny: {notification.approval_url}?action=deny
"""
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                from_addr=self.from_email,
                to_addrs=self.to_emails,
            )
            return True
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False


class ApprovalNotifier:
    """Manages multiple notifiers for approval requests."""

    def __init__(self):
        self._notifiers: list[Notifier] = []
        self._default_approval_url: Optional[str] = None

    def add_notifier(self, notifier: Notifier) -> None:
        """Add a notifier."""
        self._notifiers.append(notifier)

    def set_default_approval_url(self, url: str) -> None:
        """Set the default approval URL."""
        self._default_approval_url = url

    async def notify(
        self,
        request_id: str,
        action: str,
        description: str,
        agent_name: str,
        risk_level: str,
        approval_url: Optional[str] = None,
    ) -> dict[str, bool]:
        """Send notifications to all configured notifiers."""
        notification = ApprovalNotification(
            request_id=request_id,
            action=action,
            description=description,
            agent_name=agent_name,
            risk_level=risk_level,
            approval_url=approval_url or self._default_approval_url,
        )

        results = {}
        for i, notifier in enumerate(self._notifiers):
            name = f"notifier_{i}"
            try:
                results[name] = await notifier.send(notification)
            except Exception as e:
                logger.error(f"Notifier {name} failed: {e}")
                results[name] = False

        return results