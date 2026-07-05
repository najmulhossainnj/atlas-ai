"""Real-time risk monitoring."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass
class RiskAlert:
    """A risk alert."""
    id: str
    level: str
    message: str
    metric: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RiskMonitor:
    """Real-time risk monitoring."""

    def __init__(self):
        self._alerts: list[RiskAlert] = []
        self._thresholds: dict[str, float] = {}
        self._callbacks: list[Callable] = []
        self._running = False

    def set_threshold(self, metric: str, threshold: float) -> None:
        """Set alert threshold for a metric."""
        self._thresholds[metric] = threshold

    def add_alert_callback(self, callback: Callable) -> None:
        """Add a callback for alerts."""
        self._callbacks.append(callback)

    async def check_metric(self, metric: str, value: float) -> Optional[RiskAlert]:
        """Check a metric against its threshold."""
        threshold = self._thresholds.get(metric)
        if threshold is None:
            return None
        
        if abs(value) > threshold:
            alert = RiskAlert(
                id=f"alert_{len(self._alerts)}",
                level="high" if abs(value) > threshold * 1.5 else "medium",
                message=f"{metric} exceeded threshold: {value} > {threshold}",
                metric=metric,
                value=value,
                threshold=threshold,
            )
            
            self._alerts.append(alert)
            
            for callback in self._callbacks:
                try:
                    await callback(alert)
                except Exception:
                    pass
            
            return alert
        
        return None

    async def start_monitoring(self, interval: float = 60.0) -> None:
        """Start continuous monitoring."""
        self._running = True
        
        while self._running:
            await asyncio.sleep(interval)

    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._running = False

    def get_recent_alerts(self, limit: int = 10) -> list[RiskAlert]:
        """Get recent alerts."""
        return self._alerts[-limit:]

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self._alerts.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get monitor statistics."""
        return {
            "active_alerts": len(self._alerts),
            "thresholds": self._thresholds,
            "monitoring": self._running,
        }