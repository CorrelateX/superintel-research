"""Storage boundary for loading observed market bars."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

import pandas as pd


class MarketDataStore(Protocol):
    """Minimal read interface consumed by public research examples."""

    def load_bars(
        self,
        symbols: list[str],
        *,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """Return observed bars ordered by timestamp and symbol."""
        ...
