"""Approval workflow engine."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """A request for human approval."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    description: str = ""
    agent_id: str = ""
    agent_name: str = ""
    risk_level: str = "medium"
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    requested_by: Optional[str] = None
    approved_by: Optional[str] = None
    denied_by: Optional[str] = None
    reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 3600


class ApprovalManager:
    """Manages approval workflow for risky actions."""

    def __init__(self, default_timeout: int = 3600):
        self.default_timeout = default_timeout
        self._pending_requests: dict[str, ApprovalRequest] = {}
        self._approved_callbacks: dict[str, list[Callable]] = {}
        self._denied_callbacks: dict[str, list[Callable]] = {}
        self._lock = asyncio.Lock()

    async def request_approval(
        self,
        action: str,
        description: str,
        agent_id: str = "",
        agent_name: str = "",
        risk_level: str = "medium",
        metadata: Optional[dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> ApprovalRequest:
        """Request approval for an action."""
        request = ApprovalRequest(
            action=action,
            description=description,
            agent_id=agent_id,
            agent_name=agent_name,
            risk_level=risk_level,
            metadata=metadata or {},
            timeout_seconds=timeout or self.default_timeout,
        )

        async with self._lock:
            self._pending_requests[request.id] = request

        logger.info(f"Approval requested: {action} by {agent_name} (risk: {risk_level})")

        return request

    async def approve(
        self,
        request_id: str,
        approved_by: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Approve a pending request."""
        async with self._lock:
            request = self._pending_requests.get(request_id)
            if not request or request.status != ApprovalStatus.PENDING:
                return False

            request.status = ApprovalStatus.APPROVED
            request.approved_by = approved_by
            request.responded_at = datetime.utcnow()
            request.reason = reason

        logger.info(f"Approval granted for {request.action} by {approved_by}")

        for callback in self._approved_callbacks.get(request_id, []):
            try:
                await callback(request)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        return True

    async def deny(
        self,
        request_id: str,
        denied_by: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Deny a pending request."""
        async with self._lock:
            request = self._pending_requests.get(request_id)
            if not request or request.status != ApprovalStatus.PENDING:
                return False

            request.status = ApprovalStatus.DENIED
            request.denied_by = denied_by
            request.responded_at = datetime.utcnow()
            request.reason = reason

        logger.info(f"Approval denied for {request.action} by {denied_by}: {reason}")

        for callback in self._denied_callbacks.get(request_id, []):
            try:
                await callback(request)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        return True

    async def cancel(self, request_id: str) -> bool:
        """Cancel a pending request."""
        async with self._lock:
            request = self._pending_requests.get(request_id)
            if not request or request.status != ApprovalStatus.PENDING:
                return False

            request.status = ApprovalStatus.CANCELLED
            request.responded_at = datetime.utcnow()

        return True

    async def get_pending(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        async with self._lock:
            return [
                r for r in self._pending_requests.values()
                if r.status == ApprovalStatus.PENDING
            ]

    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request."""
        async with self._lock:
            return self._pending_requests.get(request_id)

    async def register_approval_callback(
        self,
        request_id: str,
        callback: Callable,
    ) -> None:
        """Register a callback for approval."""
        if request_id not in self._approved_callbacks:
            self._approved_callbacks[request_id] = []
        self._approved_callbacks[request_id].append(callback)

    async def register_denial_callback(
        self,
        request_id: str,
        callback: Callable,
    ) -> None:
        """Register a callback for denial."""
        if request_id not in self._denied_callbacks:
            self._denied_callbacks[request_id] = []
        self._denied_callbacks[request_id].append(callback)

    async def cleanup_expired(self) -> int:
        """Clean up expired requests."""
        count = 0
        async with self._lock:
            now = datetime.utcnow()
            for request_id, request in list(self._pending_requests.items()):
                if request.status == ApprovalStatus.PENDING:
                    elapsed = (now - request.requested_at).total_seconds()
                    if elapsed > request.timeout_seconds:
                        request.status = ApprovalStatus.EXPIRED
                        request.responded_at = now
                        count += 1

        return count

    def get_stats(self) -> dict[str, Any]:
        """Get approval manager statistics."""
        return {
            "pending_count": sum(
                1 for r in self._pending_requests.values()
                if r.status == ApprovalStatus.PENDING
            ),
            "total_requests": len(self._pending_requests),
        }