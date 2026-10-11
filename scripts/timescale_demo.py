"""Run the public statistical pipeline from TimescaleDB pilot bars."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd

from superintel_research.statistics.cointegration import engle_granger
from superintel_research.statistics.multiple_testing import compute_fdr_for_pairs
from superintel_research.statistics.pair_alignment import align_pair_frames
from superintel_research.storage import TimescaleMarketDataStore


PAIRS = [
    ("SYNTH_A", "SYNTH_B"),
    ("SYNTH_A", "SYNTH_C"),
    ("SYNTH_C", "SYNTH_D"),
]


def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is required")

    store = TimescaleMarketDataStore(dsn)
    start_year = int(os.environ.get("START_YEAR", "2015"))
    bars = store.load_bars(
        sorted({symbol for pair in PAIRS for symbol in pair}),
        start=datetime(start_year, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    if bars.empty:
        raise SystemExit("No pilot bars found. Run: make db-seed")

    pair_ids: list[str] = []
    p_values: list[float] = []

    for left_symbol, right_symbol in PAIRS:
        left = bars.loc[bars["symbol"] == left_symbol, ["event_time", "close"]].copy()
        right = bars.loc[bars["symbol"] == right_symbol, ["event_time", "close"]].copy()

        if left.empty or right.empty:
            print(
                f"skip {left_symbol}/{right_symbol}: no seeded bars for one leg "
                f"(run: make db-seed, or populate research.market_bars yourself)"
            )
            continue

        aligned = align_pair_frames(
            left,
            right,
            symbol_x=left_symbol,
            symbol_y=right_symbol,
            min_observations=60,
        )
        result = engle_granger(
            pd.Series(aligned.x_prices),
            pd.Series(aligned.y_prices),
            min_observations=60,
        )
        pair_ids.append(f"{left_symbol}/{right_symbol}")
        p_values.append(result.p_value)

    if not pair_ids:
        raise SystemExit("No pair had enough seeded bars. Run: make db-seed")

    adjusted = compute_fdr_for_pairs(pair_ids, p_values)
    print("pair                    p-value      q-value      FDR<5%")
    print("-" * 62)
    for pair_id, result in zip(pair_ids, adjusted, strict=True):
        print(
            f"{pair_id:22s} {result.original_pvalue:10.6f} "
            f"{result.q_value:12.6f} {str(result.is_significant_at_05):>8s}"
        )


if __name__ == "__main__":
    main()
