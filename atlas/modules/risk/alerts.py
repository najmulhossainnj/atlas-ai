"""Risk alert system."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """A risk alert."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    message: str = ""
    level: AlertLevel = AlertLevel.WARNING
    source: str = ""
    metric: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """Manages risk alerts."""

    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self._alerts: list[Alert] = []
        self._handlers: dict[AlertLevel, list] = {level: [] for level in AlertLevel}

    def subscribe(
        self,
        level: AlertLevel,
        handler: asyncio.coroutines,
    ) -> None:
        """Subscribe to alerts of a specific level."""
        self._handlers[level].append(handler)

    async def create_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.WARNING,
        source: str = "",
        **kwargs,
    ) -> Alert:
        """Create and dispatch an alert."""
        alert = Alert(
            title=title,
            message=message,
            level=level,
            source=source,
            **kwargs,
        )
        
        self._alerts.append(alert)
        
        if len(self._alerts) > self.max_alerts:
            self._alerts = self._alerts[-self.max_alerts:]
        
        for handler in self._handlers.get(alert.level, []):
            try:
                await handler(alert)
            except Exception:
                pass
        
        return alert

    async def acknowledge(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in reversed(self._alerts):
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> list[Alert]:
        """Get alerts with optional filtering."""
        alerts = self._alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        
        return alerts[-limit:]

    def clear_alerts(self, before: Optional[datetime] = None) -> int:
        """Clear old alerts."""
        count = len(self._alerts)
        
        if before:
            self._alerts = [a for a in self._alerts if a.timestamp >= before]
        else:
            self._alerts.clear()
        
        return count - len(self._alerts)