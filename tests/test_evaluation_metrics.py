import numpy as np

from superintel_research.evaluation.classification_metrics import compute_classification_metrics
from superintel_research.evaluation.trading_metrics import compute_trading_metrics


def test_classification_metrics_report_probability_quality():
    metrics = compute_classification_metrics(
        [0, 0, 1, 1],
        [0.1, 0.3, 0.7, 0.9],
    )
    assert metrics["accuracy"] == 1.0
    assert metrics["roc_auc"] == 1.0
    assert metrics["brier_score"] is not None


def test_trading_metrics_separate_economic_outcomes():
    metrics = compute_trading_metrics(np.array([0.01, -0.005, 0.02, -0.01]))
    assert metrics["trade_count"] == 4
    assert metrics["hit_rate"] == 0.5
    assert metrics["mean_net_return"] > 0
    assert metrics["max_drawdown"] <= 0
