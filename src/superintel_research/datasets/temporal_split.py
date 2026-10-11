"""Deterministic walk-forward temporal splitting with an explicit purge gap."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class WalkForwardFold:
    """One chronological fold expressed as end-exclusive row positions."""

    fold_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int

    @property
    def train_size(self) -> int:
        return self.train_end - self.train_start

    @property
    def test_size(self) -> int:
        return self.test_end - self.test_start

    @property
    def purge_size(self) -> int:
        return self.test_start - self.train_end

    def slice(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return (
            frame.iloc[self.train_start : self.train_end],
            frame.iloc[self.test_start : self.test_end],
        )


class WalkForwardSplitter:
    """Rolling chronological splitter with a gap between train and test windows."""

    def __init__(
        self,
        train_size: int,
        test_size: int,
        step_size: int | None = None,
        purge_gap: int = 0,
    ) -> None:
        if train_size <= 0 or test_size <= 0:
            raise ValueError("train_size and test_size must be positive")
        if purge_gap < 0:
            raise ValueError("purge_gap must be >= 0")

        self.train_size = train_size
        self.test_size = test_size
        self.step_size = test_size if step_size is None else step_size
        self.purge_gap = purge_gap
        if self.step_size <= 0:
            raise ValueError("step_size must be positive")

    def split(self, frame: pd.DataFrame) -> list[WalkForwardFold]:
        folds: list[WalkForwardFold] = []
        start = 0
        required = self.train_size + self.purge_gap + self.test_size

        while start + required <= len(frame):
            train_end = start + self.train_size
            test_start = train_end + self.purge_gap
            test_end = test_start + self.test_size
            folds.append(
                WalkForwardFold(
                    fold_id=len(folds),
                    train_start=start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end,
                )
            )
            start += self.step_size
        return folds
