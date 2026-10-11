"""Leakage-aware walk-forward classifier evaluation.

Preprocessing is fitted inside each training fold and never on the complete
sample. The implementation is intentionally model-agnostic and contains no
private feature engineering or ranking logic.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from superintel_research.datasets.temporal_split import WalkForwardSplitter
from superintel_research.evaluation.classification_metrics import (
    compute_classification_metrics,
)


class WalkForwardEvaluator:
    """Evaluate sklearn-style classifiers over purged temporal folds."""

    def __init__(
        self,
        splitter: WalkForwardSplitter,
        estimator_factory: Callable[[], Any],
    ) -> None:
        self.splitter = splitter
        self.estimator_factory = estimator_factory

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
        if len(X) != len(y):
            raise ValueError("X and y must have equal length")

        fold_results: list[dict[str, Any]] = []
        for fold in self.splitter.split(X):
            train_x, test_x = fold.slice(X)
            train_y = y.iloc[fold.train_start : fold.train_end]
            test_y = y.iloc[fold.test_start : fold.test_end]

            if train_y.nunique() < 2 or test_y.nunique() < 2:
                continue

            scaler = StandardScaler()
            train_scaled = scaler.fit_transform(train_x)
            test_scaled = scaler.transform(test_x)

            estimator = self.estimator_factory()
            estimator.fit(train_scaled, train_y)
            prediction = estimator.predict(test_scaled)
            score = self._positive_probability(estimator, test_scaled)

            metrics = compute_classification_metrics(
                test_y,
                score,
                y_pred=prediction,
            )
            fold_results.append({"fold_id": fold.fold_id, "metrics": metrics})

        return {
            "folds": fold_results,
            "aggregate": self._aggregate(fold_results),
        }

    @staticmethod
    def _positive_probability(estimator: Any, X: np.ndarray) -> np.ndarray | None:
        if not hasattr(estimator, "predict_proba"):
            return None
        probability = np.asarray(estimator.predict_proba(X))
        classes = list(getattr(estimator, "classes_", []))
        if classes:
            index = classes.index(1) if 1 in classes else len(classes) - 1
        else:
            index = -1
        return probability[:, index]

    @staticmethod
    def _aggregate(folds: list[dict[str, Any]]) -> dict[str, Any]:
        aggregate: dict[str, Any] = {"n_folds": len(folds)}
        if not folds:
            return aggregate

        keys = set().union(*(fold["metrics"].keys() for fold in folds))
        for key in sorted(keys):
            if key == "n_samples":
                continue
            values = [
                fold["metrics"].get(key)
                for fold in folds
                if isinstance(fold["metrics"].get(key), (int, float))
                and fold["metrics"].get(key) is not None
            ]
            finite = [float(value) for value in values if np.isfinite(value)]
            aggregate[f"mean_{key}"] = float(np.mean(finite)) if finite else None
        return aggregate
