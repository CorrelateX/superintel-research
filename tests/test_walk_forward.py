import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from superintel_research.datasets.temporal_split import WalkForwardSplitter
from superintel_research.evaluation.walk_forward import WalkForwardEvaluator


def test_walk_forward_evaluator_runs_multiple_temporal_folds():
    rng = np.random.default_rng(11)
    n = 260
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    target = (x1 + 0.2 * x2 > 0).astype(int)
    X = pd.DataFrame({"x1": x1, "x2": x2})
    y = pd.Series(target)

    evaluator = WalkForwardEvaluator(
        WalkForwardSplitter(train_size=100, test_size=40, step_size=40, purge_gap=2),
        lambda: LogisticRegression(max_iter=500),
    )
    result = evaluator.evaluate(X, y)

    assert result["aggregate"]["n_folds"] >= 2
    assert result["aggregate"]["mean_accuracy"] is not None
