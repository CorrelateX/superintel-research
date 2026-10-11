import numpy as np
import pandas as pd

from superintel_research.statistics.cointegration import engle_granger


def test_cointegrated_synthetic_pair_has_small_pvalue():
    rng = np.random.default_rng(7)
    n = 400
    x = 100 + np.cumsum(rng.normal(0, 0.5, n))
    y = 15 + 1.2 * x + rng.normal(0, 0.25, n)

    result = engle_granger(pd.Series(y), pd.Series(x))

    assert result.observations == n
    assert result.p_value < 0.05
    assert np.isfinite(result.hedge_ratio)


def test_identical_legs_are_rejected():
    series = pd.Series(np.linspace(100, 120, 100))
    try:
        engle_granger(series, series)
    except ValueError:
        pass
    else:
        raise AssertionError("self-comparison must be rejected")
