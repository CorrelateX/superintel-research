"""Benjamini-Hochberg false-discovery-rate control for research candidate families."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FDRResult:
    """Adjusted result for one hypothesis."""

    original_pvalue: float
    q_value: float
    rank: int
    is_significant_at_05: bool
    is_significant_at_10: bool


def compute_family_id(
    universe: list[str],
    granularity: str,
    lookback_days: int,
    fdr_alpha: float,
    eligibility_policy: str = "all_valid_pairs",
) -> str:
    """Return a deterministic identifier for one multiple-testing family."""
    payload = json.dumps(
        {
            "universe": sorted(universe),
            "granularity": granularity,
            "lookback_days": lookback_days,
            "fdr_alpha": fdr_alpha,
            "eligibility_policy": eligibility_policy,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "fam_" + hashlib.sha256(payload).hexdigest()[:16]


def benjamini_hochberg_adjust(pvalues: list[float]) -> list[float]:
    """Return BH-adjusted q-values in the same order as the input.

    NaN positions are retained and excluded from the effective hypothesis count.
    Finite p-values must lie in [0, 1].
    """
    if not pvalues:
        return []

    values = np.asarray(pvalues, dtype=float)
    finite = np.isfinite(values)
    valid_values = values[finite]
    if np.any((valid_values < 0.0) | (valid_values > 1.0)):
        raise ValueError("finite p-values must lie in [0, 1]")
    if len(valid_values) == 0:
        return np.full(len(values), np.nan).tolist()

    order = np.argsort(valid_values, kind="mergesort")
    sorted_values = valid_values[order]
    ranks = np.arange(1, len(sorted_values) + 1, dtype=float)
    raw = len(sorted_values) * sorted_values / ranks
    adjusted_sorted = np.minimum.accumulate(raw[::-1])[::-1]
    adjusted_sorted = np.clip(adjusted_sorted, 0.0, 1.0)

    adjusted_valid = np.empty_like(adjusted_sorted)
    adjusted_valid[order] = adjusted_sorted
    result = np.full(len(values), np.nan)
    result[finite] = adjusted_valid
    return result.tolist()


def compute_fdr_for_pairs(
    pair_ids: list[str],
    pvalues: list[float | None],
) -> list[FDRResult]:
    """Adjust one family of pair-level p-values and return significance flags."""
    if len(pair_ids) != len(pvalues):
        raise ValueError("pair_ids and pvalues must have the same length")

    cleaned = [np.nan if value is None else float(value) for value in pvalues]
    qvalues = benjamini_hochberg_adjust(cleaned)

    finite_values = np.asarray(cleaned, dtype=float)
    finite_sorted = np.sort(finite_values[np.isfinite(finite_values)])
    results: list[FDRResult] = []
    for pvalue, qvalue in zip(cleaned, qvalues, strict=True):
        if not np.isfinite(pvalue) or not np.isfinite(qvalue):
            results.append(
                FDRResult(
                    original_pvalue=float("nan"),
                    q_value=float("nan"),
                    rank=0,
                    is_significant_at_05=False,
                    is_significant_at_10=False,
                )
            )
            continue

        rank = int(np.searchsorted(finite_sorted, pvalue, side="left") + 1)
        results.append(
            FDRResult(
                original_pvalue=float(pvalue),
                q_value=float(qvalue),
                rank=rank,
                is_significant_at_05=bool(qvalue <= 0.05),
                is_significant_at_10=bool(qvalue <= 0.10),
            )
        )
    return results


def filter_pairs_by_fdr(
    pair_ids: list[str],
    pvalues: list[float | None],
    fdr_threshold: float = 0.05,
) -> list[str]:
    """Return pair identifiers whose BH-adjusted q-value is within the threshold."""
    if not 0.0 <= fdr_threshold <= 1.0:
        raise ValueError("fdr_threshold must lie in [0, 1]")
    results = compute_fdr_for_pairs(pair_ids, pvalues)
    return [
        pair_id
        for pair_id, result in zip(pair_ids, results, strict=True)
        if np.isfinite(result.q_value) and result.q_value <= fdr_threshold
    ]
