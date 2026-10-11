"""Economic outcome metrics kept separate from model-classification metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_trading_metrics(
    returns: Any = None,
    *,
    signal: Any = None,
    periods_per_year: float = 252,
) -> dict[str, float | int | None]:
    """Summarize finite per-trade net returns without making profitability claims."""
    values = _extract_net_returns(returns, signal)
    output: dict[str, float | int | None] = {
        "trade_count": len(values),
        "hit_rate": None,
        "mean_net_return": None,
        "profit_factor": None,
        "sharpe": None,
        "max_drawdown": 0.0,
        "periods_per_year": float(periods_per_year),
    }
    if len(values) == 0:
        return output

    wins = values[values > 0]
    losses = values[values < 0]
    output["hit_rate"] = float(len(wins) / len(values))
    output["mean_net_return"] = float(np.mean(values))

    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())
    output["profit_factor"] = gross_win / gross_loss if gross_loss > 0 else None

    if len(values) >= 2:
        volatility = float(np.std(values, ddof=1))
        if volatility > 0:
            output["sharpe"] = float(
                np.mean(values) / volatility * np.sqrt(periods_per_year)
            )

    equity = np.cumprod(1.0 + values)
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max
    output["max_drawdown"] = float(np.min(drawdown))
    return output


def _extract_net_returns(returns: Any, signal: Any) -> np.ndarray:
    if returns is None:
        return np.array([], dtype=float)

    selected_signal: np.ndarray | None = None
    if isinstance(returns, pd.DataFrame):
        if "net_return" in returns.columns:
            column = "net_return"
        elif "return" in returns.columns:
            column = "return"
        else:
            raise ValueError("DataFrame must contain 'net_return' or 'return'")
        values = returns[column].to_numpy(dtype=float)
        if signal is not None:
            selected_signal = np.asarray(signal, dtype=float).ravel()
        elif "signal" in returns.columns:
            selected_signal = returns["signal"].to_numpy(dtype=float)
    else:
        values = np.asarray(returns, dtype=float).ravel()
        if signal is not None:
            selected_signal = np.asarray(signal, dtype=float).ravel()

    finite = np.isfinite(values)
    values = values[finite]
    if selected_signal is not None:
        if len(selected_signal) != len(finite):
            raise ValueError("signal and returns must have the same length")
        selected_signal = selected_signal[finite]
        values = values[np.isfinite(selected_signal) & (selected_signal != 0)]
    return values
