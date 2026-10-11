"""Market Exchange Holiday Calendar Engine for market-day filtering and timestamp alignment."""

from __future__ import annotations

import os
from datetime import date, datetime
import pandas as pd


class ExchangeCalendar:
    """Utility class to filter exchange holidays and verify trading day validity."""

    def __init__(self, csv_path: str | None = None) -> None:
        if csv_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            csv_path = os.path.join(base_dir, "holiday_data", "exchange_holidays.csv")

        self.holidays: set[tuple[str, date]] = set()
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                try:
                    d = pd.to_datetime(row["date"]).date()
                    self.holidays.add((str(row["exchange"]).upper(), d))
                except Exception:
                    continue

    def is_trading_day(self, dt: date | datetime, exchange: str = "NYSE") -> bool:
        """Return True if dt is a valid trading day (weekday and non-holiday)."""
        if isinstance(dt, datetime):
            dt = dt.date()

        # Weekends (5 = Saturday, 6 = Sunday)
        if dt.weekday() >= 5:
            return False

        # Exchange Holiday
        if (exchange.upper(), dt) in self.holidays:
            return False

        return True

    def filter_trading_days(self, df: pd.DataFrame, time_column: str = "event_time", exchange: str = "NYSE") -> pd.DataFrame:
        """Filter out weekend and exchange holiday observations from DataFrame."""
        if df.empty or time_column not in df.columns:
            return df

        timestamps = pd.to_datetime(df[time_column])
        valid_mask = timestamps.map(lambda ts: self.is_trading_day(ts.date(), exchange=exchange))
        return df[valid_mask].reset_index(drop=True)
