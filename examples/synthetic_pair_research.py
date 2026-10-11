"""Seeded synthetic demonstration of the public research pipeline.

The example intentionally uses generated data. It demonstrates temporal
alignment, Engle-Granger testing and FDR control without publishing private
market data, pair universes, ranking logic or trading parameters.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from superintel_research.statistics.cointegration import engle_granger
from superintel_research.statistics.multiple_testing import compute_fdr_for_pairs
from superintel_research.statistics.pair_alignment import align_pair_frames


def _cointegrated_pair(rng: np.random.Generator, periods: int, beta: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    time = pd.date_range("2024-01-01", periods=periods, freq="D", tz="UTC")
    common = 100 + np.cumsum(rng.normal(0, 0.7, periods))
    x = common + rng.normal(0, 0.2, periods)
    y = 20 + beta * common + rng.normal(0, 0.4, periods)

    left = pd.DataFrame({"event_time": time, "close": y})
    right = pd.DataFrame({"event_time": time, "close": x})

    # Remove different observations from each leg to prove alignment is timestamp-based.
    left = left.drop(index=[11, 73]).reset_index(drop=True)
    right = right.drop(index=[19, 73, 121]).reset_index(drop=True)
    return left, right


def _independent_pair(rng: np.random.Generator, periods: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    time = pd.date_range("2024-01-01", periods=periods, freq="D", tz="UTC")
    x = 100 + np.cumsum(rng.normal(0, 1.0, periods))
    y = 120 + np.cumsum(rng.normal(0, 1.0, periods))
    return (
        pd.DataFrame({"event_time": time, "close": y}),
        pd.DataFrame({"event_time": time, "close": x}),
    )


def main() -> None:
    rng = np.random.default_rng(42)
    pair_ids: list[str] = []
    p_values: list[float] = []

    for index in range(6):
        pair_id = f"SYNTH-{index + 1}"
        if index < 3:
            y_frame, x_frame = _cointegrated_pair(rng, periods=320, beta=0.8 + index * 0.1)
        else:
            y_frame, x_frame = _independent_pair(rng, periods=320)

        aligned = align_pair_frames(
            y_frame,
            x_frame,
            symbol_x=f"{pair_id}-Y",
            symbol_y=f"{pair_id}-X",
            min_observations=60,
        )
        result = engle_granger(
            pd.Series(aligned.x_prices),
            pd.Series(aligned.y_prices),
            min_observations=60,
        )
        pair_ids.append(pair_id)
        p_values.append(result.p_value)

    adjusted = compute_fdr_for_pairs(pair_ids, p_values)
    print("pair       p-value      q-value      FDR<5%")
    print("-" * 49)
    for pair_id, result in zip(pair_ids, adjusted, strict=True):
        print(
            f"{pair_id:10s} {result.original_pvalue:10.6f} "
            f"{result.q_value:12.6f} {str(result.is_significant_at_05):>8s}"
        )


if __name__ == "__main__":
    main()
