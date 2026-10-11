import numpy as np

from superintel_research.statistics.multiple_testing import (
    benjamini_hochberg_adjust,
    compute_family_id,
    compute_fdr_for_pairs,
)


def test_bh_known_values_and_order():
    q = benjamini_hochberg_adjust([0.01, 0.04, 0.20])
    assert np.allclose(q, [0.03, 0.06, 0.20])


def test_bh_preserves_nan_positions():
    q = benjamini_hochberg_adjust([0.01, np.nan, 0.20])
    assert np.isnan(q[1])
    assert q[0] <= q[2]


def test_family_identity_is_order_independent_but_configuration_sensitive():
    first = compute_family_id(["A", "B", "C"], "1d", 90, 0.05)
    reordered = compute_family_id(["C", "A", "B"], "1d", 90, 0.05)
    changed = compute_family_id(["A", "B", "C"], "1d", 120, 0.05)
    assert first == reordered
    assert first != changed


def test_fdr_result_flags():
    results = compute_fdr_for_pairs(["A/B", "C/D"], [0.001, 0.8])
    assert results[0].is_significant_at_05
    assert not results[1].is_significant_at_05
