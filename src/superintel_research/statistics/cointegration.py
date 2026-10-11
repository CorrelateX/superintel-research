"""Sanitized Engle-Granger reference implementation for research demonstrations.

This module deliberately stops at statistical diagnostics. Candidate scoring,
ranking, signal thresholds, position sizing, and execution logic are outside the
public repository boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint


@dataclass(frozen=True)
class CointegrationResult:
    """Statistical diagnostics for one aligned pair."""

    test_statistic: float
    p_value: float
    critical_values: tuple[float, float, float]
    hedge_ratio: float
    intercept: float
    residual_adf_statistic: float
    residual_adf_p_value: float
    half_life_periods: float
    observations: int


def engle_granger(
    y: pd.Series,
    x: pd.Series,
    *,
    min_observations: int = 60,
) -> CointegrationResult:
    """Run an Engle-Granger test on already time-aligned positive price series.

    The orientation is deterministic: ``y = intercept + beta * x + residual``.
    No ranking or trading decision is produced.
    """
    yv, xv = _validate_pair(y, x, min_observations=min_observations)

    test_stat, p_value, critical = coint(yv, xv, trend="c", autolag="AIC")
    design = sm.add_constant(xv)
    fit = sm.OLS(yv, design).fit()
    intercept = float(fit.params[0])
    beta = float(fit.params[1])
    residuals = pd.Series(yv - intercept - beta * xv)
    adf = adfuller(residuals, autolag="AIC")

    return CointegrationResult(
        test_statistic=float(test_stat),
        p_value=float(p_value),
        critical_values=tuple(float(v) for v in critical),
        hedge_ratio=beta,
        intercept=intercept,
        residual_adf_statistic=float(adf[0]),
        residual_adf_p_value=float(adf[1]),
        half_life_periods=_half_life(residuals),
        observations=len(yv),
    )


def _validate_pair(
    y: pd.Series,
    x: pd.Series,
    *,
    min_observations: int,
) -> tuple[np.ndarray, np.ndarray]:
    if len(y) != len(x):
        raise ValueError("pair legs must have equal length after temporal alignment")
    if len(y) < min_observations:
        raise ValueError(f"need at least {min_observations} aligned observations")

    yv = np.asarray(y, dtype=float)
    xv = np.asarray(x, dtype=float)
    if not np.isfinite(yv).all() or not np.isfinite(xv).all():
        raise ValueError("pair contains non-finite values")
    if (yv <= 0).any() or (xv <= 0).any():
        raise ValueError("price series must be strictly positive")
    if np.array_equal(yv, xv):
        raise ValueError("pair legs must be distinct")
    return yv, xv


def _half_life(residuals: pd.Series) -> float:
    """Estimate AR(1) mean-reversion half-life in observation periods."""
    lagged = residuals.shift(1).dropna().to_numpy(dtype=float)
    current = residuals.iloc[1:].to_numpy(dtype=float)
    if len(lagged) < 10:
        return float("inf")

    fit = sm.OLS(current, sm.add_constant(lagged)).fit()
    phi = float(fit.params[1])
    if not np.isfinite(phi) or not 0.0 < phi < 1.0:
        return float("inf")
    return float(-np.log(2.0) / np.log(phi))
