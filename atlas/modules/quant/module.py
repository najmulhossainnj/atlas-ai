"""Quantitative finance module."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
import json


@dataclass
class MarketData:
    """Market data for a security."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Factor:
    """A quantitative factor."""
    name: str
    description: str
    values: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Results of a backtest."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades: list[dict[str, Any]] = field(default_factory=list)


class QuantModule:
    """Module for quantitative finance tasks."""

    def __init__(
        self,
        data_provider: Optional[Any] = None,
        risk_free_rate: float = 0.02,
    ):
        self.data_provider = data_provider
        self.risk_free_rate = risk_free_rate
        self._market_cache: dict[str, list[MarketData]] = {}
        self._factors: dict[str, Factor] = {}

    async def fetch_market_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> list[MarketData]:
        """Fetch market data for a symbol."""
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        
        if cache_key in self._market_cache:
            return self._market_cache[cache_key]

        if self.data_provider:
            data = await self.data_provider.get_data(symbol, start_date, end_date)
        else:
            data = self._generate_sample_data(symbol, start_date, end_date)

        self._market_cache[cache_key] = data
        return data

    def _generate_sample_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MarketData]:
        """Generate sample market data for testing."""
        import random
        
        data = []
        current_date = start_date
        price = 100.0
        
        while current_date <= end_date:
            if current_date.weekday() < 5:
                change = random.uniform(-0.03, 0.03)
                open_price = price
                close_price = price * (1 + change)
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
                volume = random.randint(100000, 1000000)
                
                data.append(MarketData(
                    symbol=symbol,
                    timestamp=current_date,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                ))
                
                price = close_price
            current_date += timedelta(days=1)
        
        return data

    async def calculate_returns(
        self,
        prices: list[float],
    ) -> list[float]:
        """Calculate returns from prices."""
        if len(prices) < 2:
            return []
        
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        
        return returns

    async def calculate_volatility(
        self,
        returns: list[float],
        window: int = 20,
    ) -> list[float]:
        """Calculate rolling volatility."""
        if len(returns) < window:
            return []
        
        volatilities = []
        for i in range(window, len(returns) + 1):
            window_returns = returns[i-window:i]
            mean_return = sum(window_returns) / len(window_returns)
            variance = sum((r - mean_return) ** 2 for r in window_returns) / len(window_returns)
            volatility = variance ** 0.5 * (252 ** 0.5)
            volatilities.append(volatility)
        
        return volatilities

    async def calculate_sharpe_ratio(
        self,
        returns: list[float],
        risk_free_rate: Optional[float] = None,
    ) -> float:
        """Calculate Sharpe ratio."""
        if not returns:
            return 0.0
        
        rfr = risk_free_rate or self.risk_free_rate / 252
        
        excess_returns = [r - rfr for r in returns]
        mean_excess = sum(excess_returns) / len(excess_returns)
        
        if len(excess_returns) < 2:
            return 0.0
        
        std_dev = (sum((r - mean_excess) ** 2 for r in excess_returns) / len(excess_returns)) ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        return (mean_excess / std_dev) * (252 ** 0.5)

    async def calculate_max_drawdown(
        self,
        prices: list[float],
    ) -> float:
        """Calculate maximum drawdown."""
        if not prices:
            return 0.0
        
        peak = prices[0]
        max_dd = 0.0
        
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd

    async def run_backtest(
        self,
        strategy_fn: Any,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
    ) -> BacktestResult:
        """Run a backtest for a strategy."""
        prices = await self.fetch_market_data(symbol, start_date, end_date)
        
        if not prices:
            return BacktestResult(
                strategy_name=strategy_fn.__name__,
                start_date=start_date,
                end_date=end_date,
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
            )

        close_prices = [p.close for p in prices]
        returns = await self.calculate_returns(close_prices)
        
        capital = initial_capital
        position = 0
        trades = []
        wins = 0
        losses = 0
        
        for i, (price, ret) in enumerate(zip(close_prices[1:], returns)):
            signal = strategy_fn(returns=max(0, i-20), prices=close_prices[max(0, i-20):i+1])
            
            if signal == "BUY" and position == 0:
                position = capital / price
                capital = 0
                trades.append({"action": "BUY", "price": price, "date": prices[i+1].timestamp})
            elif signal == "SELL" and position > 0:
                capital = position * price
                position = 0
                trades.append({"action": "SELL", "price": price, "date": prices[i+1].timestamp})
                if capital > initial_capital:
                    wins += 1
                else:
                    losses += 1

        if position > 0:
            capital = position * close_prices[-1]
        
        total_return = (capital - initial_capital) / initial_capital
        sharpe = await self.calculate_sharpe_ratio(returns)
        max_dd = await self.calculate_max_drawdown(close_prices)
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.0

        return BacktestResult(
            strategy_name=strategy_fn.__name__,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            trades=trades,
        )

    async def create_factor(
        self,
        name: str,
        description: str,
        values: list[float],
        metadata: Optional[dict[str, Any]] = None,
    ) -> Factor:
        """Create a quantitative factor."""
        factor = Factor(
            name=name,
            description=description,
            values=values,
            metadata=metadata or {},
        )
        self._factors[name] = factor
        return factor

    async def get_factor_correlation(
        self,
        factor1: str,
        factor2: str,
    ) -> float:
        """Calculate correlation between two factors."""
        if factor1 not in self._factors or factor2 not in self._factors:
            return 0.0

        f1 = self._factors[factor1].values
        f2 = self._factors[factor2].values

        if len(f1) != len(f2) or len(f1) == 0:
            return 0.0

        mean1 = sum(f1) / len(f1)
        mean2 = sum(f2) / len(f2)

        numerator = sum((a - mean1) * (b - mean2) for a, b in zip(f1, f2))
        denom1 = sum((a - mean1) ** 2 for a in f1) ** 0.5
        denom2 = sum((b - mean2) ** 2 for b in f2) ** 0.5

        if denom1 == 0 or denom2 == 0:
            return 0.0

        return numerator / (denom1 * denom2)

    def get_stats(self) -> dict[str, Any]:
        """Get quant module statistics."""
        return {
            "cached_symbols": len(self._market_cache),
            "factors_defined": len(self._factors),
            "risk_free_rate": self.risk_free_rate,
        }
