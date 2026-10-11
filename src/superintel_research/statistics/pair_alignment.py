"""Canonical timestamp alignment for two independently observed price series.

The key invariant is simple: equal array length does not imply equal market time.
Pair legs are aligned on observed timestamps, duplicates are resolved by an
explicit policy, and missing observations are never forward-filled.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DEFAULT_TIME_COLUMNS = ("event_time", "timestamp", "date")
DEFAULT_PRICE_COLUMNS = ("close", "Close")


def _resolve_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    return next((column for column in candidates if column in df.columns), None)


@dataclass(frozen=True)
class AlignedPairSeries:
    """Two positive finite price arrays sharing one ordered timestamp index."""

    symbol_x: str
    symbol_y: str
    event_time: pd.DatetimeIndex
    x_prices: np.ndarray
    y_prices: np.ndarray
    granularity: str
    raw_x_count: int
    raw_y_count: int

    @property
    def aligned_count(self) -> int:
        return len(self.event_time)

    @property
    def overlap_ratio(self) -> float:
        denominator = max(self.raw_x_count, self.raw_y_count)
        return self.aligned_count / denominator if denominator else 0.0


def align_pair_frames(
    df_x: pd.DataFrame,
    df_y: pd.DataFrame,
    symbol_x: str,
    symbol_y: str,
    granularity: str = "daily",
    time_column: str | None = None,
    price_column: str | None = None,
    dedup: str = "last",
    min_observations: int = 2,
) -> AlignedPairSeries:
    """Return two price arrays aligned on their genuinely shared observations."""
    if dedup not in {"first", "last"}:
        raise ValueError(f"dedup must be 'first' or 'last', got {dedup!r}")
    if min_observations < 1:
        raise ValueError("min_observations must be >= 1")

    time_x = time_column or _resolve_column(df_x, DEFAULT_TIME_COLUMNS)
    time_y = time_column or _resolve_column(df_y, DEFAULT_TIME_COLUMNS)
    price_x = price_column or _resolve_column(df_x, DEFAULT_PRICE_COLUMNS)
    price_y = price_column or _resolve_column(df_y, DEFAULT_PRICE_COLUMNS)

    if time_x is None or time_y is None:
        raise ValueError("both legs require a recognized timestamp column")
    if price_x is None or price_y is None:
        raise ValueError("both legs require a recognized price column")

    raw_x_count = len(df_x)
    raw_y_count = len(df_y)

    series_x = _canonical_series(df_x, time_x, price_x, symbol_x, dedup)
    series_y = _canonical_series(df_y, time_y, price_y, symbol_y, dedup)

    common = series_x.index.intersection(series_y.index).sort_values()
    if len(common) < min_observations:
        raise ValueError(
            f"insufficient overlap for {symbol_x}/{symbol_y}: "
            f"{len(common)} < {min_observations}"
        )

    x = series_x.loc[common].to_numpy(dtype=float)
    y = series_y.loc[common].to_numpy(dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("aligned prices must be finite")
    if (x <= 0).any() or (y <= 0).any():
        raise ValueError("aligned prices must be strictly positive")

    event_time = pd.DatetimeIndex(common)
    if not event_time.is_monotonic_increasing:
        raise ValueError("aligned timestamps must be monotonic increasing")

    return AlignedPairSeries(
        symbol_x=symbol_x,
        symbol_y=symbol_y,
        event_time=event_time,
        x_prices=x,
        y_prices=y,
        granularity=granularity,
        raw_x_count=raw_x_count,
        raw_y_count=raw_y_count,
    )


def _canonical_series(
    frame: pd.DataFrame,
    time_column: str,
    price_column: str,
    symbol: str,
    dedup: str,
) -> pd.Series:
    working = frame[[time_column, price_column] + (["created_at"] if "created_at" in frame else [])].copy()
    working[time_column] = pd.to_datetime(working[time_column], utc=True)
    sort_columns = [time_column] + (["created_at"] if "created_at" in working else [])
    working = working.sort_values(sort_columns, kind="mergesort")
    working = working.drop_duplicates(subset=[time_column], keep=dedup)
    series = working.set_index(time_column)[price_column].astype(float)
    series.name = symbol
    return series
