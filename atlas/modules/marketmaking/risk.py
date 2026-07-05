"""Market making risk manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RiskLimits:
    """Risk management limits."""
    max_position: float = 10000.0
    max_daily_loss: float = 1000.0
    max_spread: float = 0.1
    min_spread: float = 0.001


class MM_RiskManager:
    """Risk manager for market making."""

    def __init__(self, limits: RiskLimits | None = None):
        self.limits = limits or RiskLimits()
        self.daily_pnl = 0.0
        self.positions: dict[str, float] = {}

    def check_position_limit(self, symbol: str, new_position: float) -> tuple[bool, str]:
        """Check if position exceeds limits."""
        if abs(new_position) > self.limits.max_position:
            return False, f"Position {new_position} exceeds limit {self.limits.max_position}"
        return True, ""

    def check_daily_loss(self) -> tuple[bool, str]:
        """Check if daily loss limit is breached."""
        if self.daily_pnl < -self.limits.max_daily_loss:
            return False, f"Daily loss {self.daily_pnl} exceeds limit {-self.limits.max_daily_loss}"
        return True, ""

    def update_position(self, symbol: str, quantity: float, price: float) -> None:
        """Update position and PnL."""
        if symbol not in self.positions:
            self.positions[symbol] = 0.0
        
        old_pos = self.positions[symbol]
        self.positions[symbol] = old_pos + quantity
        
        cost = quantity * price
        self.daily_pnl -= cost

    def get_risk_metrics(self) -> dict[str, Any]:
        """Get current risk metrics."""
        total_position = sum(abs(v) for v in self.positions.values())
        return {
            "total_exposure": total_position,
            "daily_pnl": self.daily_pnl,
            "positions": self.positions,
            "limits": {
                "max_position": self.limits.max_position,
                "max_daily_loss": self.limits.max_daily_loss,
            },
        }