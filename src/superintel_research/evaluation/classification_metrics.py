"""Deterministic binary-classification metrics for temporal model evaluation."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_classification_metrics(
    y_true: Any,
    y_score: Any = None,
    *,
    y_pred: Any = None,
) -> dict[str, float | int | None]:
    """Compute threshold and probability metrics for a binary target."""
    truth = np.asarray(y_true, dtype=float).ravel()
    expected_length = len(truth)
    valid = np.isfinite(truth)

    score = None if y_score is None else _align(y_score, expected_length, "y_score")
    prediction = None if y_pred is None else _align(y_pred, expected_length, "y_pred")
    if score is not None:
        valid &= np.isfinite(score)
    if prediction is not None:
        valid &= np.isfinite(prediction)

    truth = truth[valid]
    if score is not None:
        score = score[valid]
    if prediction is not None:
        prediction = prediction[valid]

    result: dict[str, float | int | None] = {
        "n_samples": len(truth),
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "roc_auc": None,
        "pr_auc": None,
        "brier_score": None,
        "mean_pred_prob": None,
        "observed_rate": None,
    }
    if len(truth) == 0:
        return result

    result["observed_rate"] = float(np.mean(truth))
    classes = np.unique(truth)
    binary = len(classes) == 2
    positive_label = 1.0 if 1.0 in classes else float(classes[-1])

    if prediction is None and score is not None:
        prediction = (score >= 0.5).astype(float)

    if prediction is not None:
        result["accuracy"] = float(accuracy_score(truth, prediction))
        if binary:
            result["precision"] = float(
                precision_score(truth, prediction, pos_label=positive_label, zero_division=0)
            )
            result["recall"] = float(
                recall_score(truth, prediction, pos_label=positive_label, zero_division=0)
            )
            result["f1"] = float(
                f1_score(truth, prediction, pos_label=positive_label, zero_division=0)
            )

    if score is not None:
        result["mean_pred_prob"] = float(np.mean(score))
        result["brier_score"] = float(np.mean((score - truth) ** 2))
        if binary:
            result["roc_auc"] = float(roc_auc_score(truth, score))
            result["pr_auc"] = float(average_precision_score(truth, score))
    return result


def _align(values: Any, expected_length: int, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float).ravel()
    if len(array) != expected_length:
        raise ValueError(f"{name} must have the same length as y_true ({expected_length})")
    return array
