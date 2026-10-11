"""Optional TimescaleDB adapter for public market-bar research."""

from __future__ import annotations

from datetime import datetime

import pandas as pd


class TimescaleMarketDataStore:
    """Read OHLCV bars from the public research schema.

    The adapter deliberately exposes only observed market bars. Private feature
    stores, scores, signals, portfolio state, and execution data are outside the
    public boundary.
    """

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("dsn is required")
        self.dsn = dsn

    @staticmethod
    def _connect(dsn: str):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "Timescale support requires the 'database' extra: "
                "pip install -e '.[database]'"
            ) from exc
        return psycopg.connect(dsn)

    def load_bars(
        self,
        symbols: list[str],
        *,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        if not symbols:
            raise ValueError("symbols must not be empty")
        if start >= end:
            raise ValueError("start must be earlier than end")

        query = """
            SELECT ts, symbol, open, high, low, close, volume
            FROM research.market_bars
            WHERE symbol = ANY(%s)
              AND ts >= %s
              AND ts < %s
            ORDER BY ts ASC, symbol ASC
        """

        with self._connect(self.dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (symbols, start, end))
                rows = cursor.fetchall()

        frame = pd.DataFrame(
            rows,
            columns=["event_time", "symbol", "open", "high", "low", "close", "volume"],
        )
        if frame.empty:
            return frame

        frame["event_time"] = pd.to_datetime(frame["event_time"], utc=True)
        numeric = ["open", "high", "low", "close", "volume"]
        frame[numeric] = frame[numeric].astype(float)
        return frame
