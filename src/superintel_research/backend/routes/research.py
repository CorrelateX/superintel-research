"""Research dataset & cointegration diagnostic endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
from fastapi import APIRouter, HTTPException

from superintel_research.backend.config import settings
from superintel_research.statistics.cointegration import engle_granger
from superintel_research.statistics.multiple_testing import compute_fdr_for_pairs
from superintel_research.statistics.pair_alignment import align_pair_frames
from superintel_research.storage import TimescaleMarketDataStore

router = APIRouter(prefix="/api/v1/research", tags=["Research"])

DEFAULT_PAIRS = [
    ("SYNTH_A", "SYNTH_B"),
    ("SYNTH_A", "SYNTH_C"),
    ("SYNTH_C", "SYNTH_D"),
]


@router.get("/pairs")
def get_pair_diagnostics():
    """Return cointegration & FDR results across research pairs."""
    try:
        store = TimescaleMarketDataStore(settings.database_url)
        symbols = sorted({s for p in DEFAULT_PAIRS for s in p})
        bars = store.load_bars(
            symbols,
            start=datetime(2015, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query error: {exc}")

    if bars.empty:
        return {"pairs": [], "total_pairs": 0, "message": "No market bars found."}

    pair_ids: list[str] = []
    p_values: list[float] = []
    details: list[dict] = []

    for left_symbol, right_symbol in DEFAULT_PAIRS:
        pair_key = f"{left_symbol}/{right_symbol}"
        left = bars.loc[bars["symbol"] == left_symbol, ["event_time", "close"]].copy()
        right = bars.loc[bars["symbol"] == right_symbol, ["event_time", "close"]].copy()

        if left.empty or right.empty:
            continue

        try:
            aligned = align_pair_frames(
                left, right, symbol_x=left_symbol, symbol_y=right_symbol, min_observations=60
            )
            coint_res = engle_granger(
                pd.Series(aligned.x_prices), pd.Series(aligned.y_prices), min_observations=60
            )
            pair_ids.append(pair_key)
            p_values.append(coint_res.p_value)

            details.append({
                "pair_id": pair_key,
                "symbol_x": left_symbol,
                "symbol_y": right_symbol,
                "aligned_observations": coint_res.observations,
                "p_value": coint_res.p_value,
                "test_statistic": coint_res.test_statistic,
                "hedge_ratio": coint_res.hedge_ratio,
                "intercept": coint_res.intercept,
                "half_life_periods": coint_res.half_life_periods if pd.notna(coint_res.half_life_periods) else None,
            })
        except Exception:
            continue

    fdr_results = compute_fdr_for_pairs(pair_ids, p_values)
    for detail, fdr_res in zip(details, fdr_results, strict=True):
        detail["q_value"] = fdr_res.q_value
        detail["fdr_significant_05"] = fdr_res.is_significant_at_05

    return {
        "pairs": details,
        "total_pairs": len(details),
        "fdr_threshold": 0.05,
    }
