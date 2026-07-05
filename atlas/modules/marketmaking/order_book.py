"""Order book simulator."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Order:
    """An order in the book."""
    id: str
    side: str
    price: float
    quantity: float
    filled: float = 0.0


@dataclass
class OrderBook:
    """Simulated order book."""
    bids: list[tuple[float, float]] = field(default_factory=list)
    asks: list[tuple[float, float]] = field(default_factory=list)
    
    def add_bid(self, price: float, quantity: float) -> None:
        self.bids.append((price, quantity))
        self.bids.sort(reverse=True)
    
    def add_ask(self, price: float, quantity: float) -> None:
        self.asks.append((price, quantity))
        self.asks.sort()
    
    def get_best_bid(self) -> tuple[float, float] | None:
        return self.bids[0] if self.bids else None
    
    def get_best_ask(self) -> tuple[float, float] | None:
        return self.asks[0] if self.asks else None
    
    def get_spread(self) -> float | None:
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return best_ask[0] - best_bid[0]
        return None
    
    def get_mid_price(self) -> float | None:
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return (best_bid[0] + best_ask[0]) / 2
        return None
    
    def get_stats(self) -> dict[str, Any]:
        return {
            "bid_levels": len(self.bids),
            "ask_levels": len(self.asks),
            "best_bid": self.get_best_bid(),
            "best_ask": self.get_best_ask(),
            "spread": self.get_spread(),
            "mid_price": self.get_mid_price(),
        }