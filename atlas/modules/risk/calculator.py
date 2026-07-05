"""Risk calculation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math


@dataclass
class VaRResult:
    """Value at Risk calculation result."""
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    confidence_level_95: float
    confidence_level_99: float


class RiskCalculator:
    """Calculator for risk metrics."""

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate

    def calculate_var(
        self,
        returns: list[float],
        portfolio_value: float = 1.0,
    ) -> VaRResult:
        """Calculate Value at Risk using historical method."""
        if not returns:
            return VaRResult(0, 0, 0, 0, 1.0, 1.0)
        
        sorted_returns = sorted(returns)
        n = len(sorted_returns)
        
        var_95_idx = int(n * 0.05)
        var_99_idx = int(n * 0.01)
        
        var_95 = abs(sorted_returns[var_95_idx]) * portfolio_value if var_95_idx < n else 0
        var_99 = abs(sorted_returns[var_99_idx]) * portfolio_value if var_99_idx < n else 0
        
        cvar_95 = abs(sum(sorted_returns[:var_95_idx]) / var_95_idx * portfolio_value) if var_95_idx > 0 else 0
        cvar_99 = abs(sum(sorted_returns[:var_99_idx]) / var_99_idx * portfolio_value) if var_99_idx > 0 else 0
        
        return VaRResult(
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            confidence_level_95=0.95,
            confidence_level_99=0.99,
        )

    def calculate_sharpe_ratio(
        self,
        returns: list[float],
        risk_free_rate: float | None = None,
    ) -> float:
        """Calculate Sharpe ratio."""
        if not returns or len(returns) < 2:
            return 0.0
        
        rfr = risk_free_rate or self.risk_free_rate
        mean_return = sum(returns) / len(returns)
        
        excess_return = mean_return - rfr
        
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0.0
        
        return excess_return / std_dev

    def calculate_sortino_ratio(
        self,
        returns: list[float],
        target_return: float = 0.0,
    ) -> float:
        """Calculate Sortino ratio."""
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        downside_returns = [r for r in returns if r < target_return]
        
        if not downside_returns:
            return float("inf") if mean_return > target_return else 0.0
        
        downside_variance = sum((r - target_return) ** 2 for r in downside_returns) / len(downside_returns)
        downside_std = math.sqrt(downside_variance)
        
        if downside_std == 0:
            return 0.0
        
        return (mean_return - target_return) / downside_std

    def calculate_max_drawdown(self, values: list[float]) -> tuple[float, int, int]:
        """Calculate maximum drawdown and its duration."""
        if not values:
            return 0.0, 0, 0
        
        peak = values[0]
        peak_idx = 0
        max_dd = 0.0
        max_dd_start = 0
        max_dd_end = 0
        
        for i, value in enumerate(values):
            if value > peak:
                peak = value
                peak_idx = i
            
            drawdown = (peak - value) / peak if peak > 0 else 0
            
            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_start = peak_idx
                max_dd_end = i
        
        return max_dd, max_dd_start, max_dd_end

    def calculate_volatility(self, returns: list[float]) -> float:
        """Calculate annualized volatility."""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance * 252)