"""Market making agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MarketMakingAgent:
    """Agent for market making operations."""
    
    name: str = "MarketMaker"
    symbol: str = ""
    base_spread: float = 0.01
    position_limit: float = 10000.0
    max_position: float = 0.0
    inventory: float = 0.0
    pnl: float = 0.0
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    async def generate_quotes(self) -> dict[str, float]:
        """Generate bid and ask quotes."""
        return {
            "bid": 100.0 - self.base_spread / 2,
            "ask": 100.0 + self.base_spread / 2,
        }
    
    async def update_position(self, side: str, quantity: float, price: float) -> None:
        """Update position after trade."""
        if side == "buy":
            self.inventory += quantity
        else:
            self.inventory -= quantity
        
        self.pnl -= quantity * price if side == "buy" else -quantity * price
    
    def get_stats(self) -> dict[str, Any]:
        """Get agent statistics."""
        return {
            "name": self.name,
            "symbol": self.symbol,
            "position": self.inventory,
            "pnl": self.pnl,
            "max_position": self.max_position,
        }