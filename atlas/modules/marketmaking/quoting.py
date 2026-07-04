"""Quote generation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Quote:
    """A trading quote."""
    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: float


class QuoteEngine:
    """Engine for generating quotes."""

    def __init__(
        self,
        base_spread: float = 0.01,
        min_spread: float = 0.001,
        max_spread: float = 0.1,
        size: float = 100.0,
    ):
        self.base_spread = base_spread
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.size = size
        self._inventory = {}
        self._last_prices = {}

    def calculate_spread(
        self,
        symbol: str,
        volatility: float = 0.01,
        inventory_skew: float = 0.0,
    ) -> float:
        """Calculate dynamic spread based on conditions."""
        base = self.base_spread
        vol_adjustment = volatility * 2
        skew_adjustment = abs(inventory_skew) * 0.1
        
        spread = base + vol_adjustment + skew_adjustment
        return max(self.min_spread, min(spread, self.max_spread))

    def generate_quote(
        self,
        symbol: str,
        mid_price: float,
        volatility: float = 0.01,
        inventory: float = 0.0,
    ) -> Quote:
        """Generate a quote for a symbol."""
        inventory_skew = inventory / 10000.0
        spread = self.calculate_spread(symbol, volatility, inventory_skew)
        
        bid_price = round(mid_price * (1 - spread / 2), 2)
        ask_price = round(mid_price * (1 + spread / 2), 2)
        
        self._last_prices[symbol] = mid_price
        
        return Quote(
            symbol=symbol,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=self.size,
            ask_size=self.size,
            timestamp=__import__("time").time(),
        )

    def get_stats(self) -> dict[str, Any]:
        return {
            "base_spread": self.base_spread,
            "last_prices": self._last_prices,
        }