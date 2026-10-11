"""Seed a small deterministic synthetic OHLCV dataset into TimescaleDB."""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import numpy as np


def _make_close_series(periods: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(108)
    common = 100.0 + np.cumsum(rng.normal(0.0, 0.65, periods))
    return {
        "SYNTH_A": common + rng.normal(0.0, 0.18, periods),
        "SYNTH_B": 18.0 + 1.08 * common + rng.normal(0.0, 0.35, periods),
        "SYNTH_C": 85.0 + np.cumsum(rng.normal(0.0, 0.9, periods)),
        "SYNTH_D": 125.0 + np.cumsum(rng.normal(0.0, 1.0, periods)),
    }


def _rows(years: int | None = None) -> list[tuple]:
    if years is None:
        years = int(os.environ.get("HORIZON_YEARS", "10"))
    periods = years * 365
    rng = np.random.default_rng(109)
    closes = _make_close_series(periods)
    start = datetime(2015, 1, 1, tzinfo=timezone.utc)
    rows: list[tuple] = []

    for symbol, close_values in closes.items():
        for index, close_value in enumerate(close_values):
            ts = start + timedelta(days=index)
            open_value = float(close_value + rng.normal(0.0, 0.12))
            close_value = float(close_value)
            high_value = max(open_value, close_value) + abs(float(rng.normal(0.15, 0.05)))
            low_value = min(open_value, close_value) - abs(float(rng.normal(0.15, 0.05)))
            volume = float(rng.integers(5_000, 25_000))
            rows.append(
                (
                    ts,
                    symbol,
                    open_value,
                    high_value,
                    low_value,
                    close_value,
                    volume,
                    "pilot-synthetic-v1",
                )
            )
    return rows


def _connect_with_retry(psycopg, dsn: str, attempts: int = 12):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return psycopg.connect(dsn)
        except psycopg.OperationalError as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(1)
    assert last_error is not None
    raise last_error


def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is required")

    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("Install the database extra: pip install -e '.[database]'") from exc

    rows = _rows()
    with _connect_with_retry(psycopg, dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM research.market_bars WHERE source = %s",
                ("pilot-synthetic-v1",),
            )
            cursor.executemany(
                """
                INSERT INTO research.market_bars
                    (ts, symbol, open, high, low, close, volume, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, ts) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    source = EXCLUDED.source
                """,
                rows,
            )

    print(f"Seeded {len(rows)} deterministic pilot bars across 4 synthetic symbols")


if __name__ == "__main__":
    main()
