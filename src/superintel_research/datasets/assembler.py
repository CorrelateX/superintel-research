"""Deterministic feature/label alignment and research dataset identity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DatasetSnapshot:
    """An aligned feature/label dataset with deterministic schema metadata."""

    snapshot_id: str
    feature_schema_hash: str
    features: pd.DataFrame
    labels: pd.DataFrame
    window_metadata: dict[str, Any]

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(self.features.columns)

    @property
    def label_names(self) -> tuple[str, ...]:
        return tuple(self.labels.columns)

    @property
    def row_count(self) -> int:
        return len(self.features)


class DatasetAssembler:
    """Align features and labels on a shared ordered index."""

    @staticmethod
    def feature_schema_hash(feature_names: list[str]) -> str:
        payload = ",".join(sorted(feature_names)).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]

    def assemble(
        self,
        features: pd.DataFrame,
        labels: pd.DataFrame,
        window_metadata: dict[str, Any] | None = None,
        snapshot_id: str | None = None,
    ) -> DatasetSnapshot:
        common = features.index.intersection(labels.index).sort_values()
        if common.empty:
            raise ValueError("features and labels share no common index")

        feature_frame = features.loc[common]
        label_frame = labels.loc[common]
        valid = feature_frame.notna().all(axis=1) & label_frame.notna().all(axis=1)
        feature_frame = feature_frame.loc[valid]
        label_frame = label_frame.loc[valid]

        schema_hash = self.feature_schema_hash(list(feature_frame.columns))
        metadata = dict(window_metadata or {})
        metadata.setdefault(
            "index_start",
            feature_frame.index[0].isoformat() if len(feature_frame) else None,
        )
        metadata.setdefault(
            "index_end",
            feature_frame.index[-1].isoformat() if len(feature_frame) else None,
        )
        metadata.setdefault("row_count", len(feature_frame))

        identity = snapshot_id or self._snapshot_id(
            schema_hash,
            metadata,
            list(label_frame.columns),
            self._frame_hash(feature_frame),
            self._frame_hash(label_frame),
        )
        return DatasetSnapshot(
            snapshot_id=identity,
            feature_schema_hash=schema_hash,
            features=feature_frame,
            labels=label_frame,
            window_metadata=metadata,
        )

    @staticmethod
    def _snapshot_id(
        schema_hash: str,
        metadata: dict[str, Any],
        label_names: list[str],
        feature_data_hash: str,
        label_data_hash: str,
    ) -> str:
        payload = json.dumps(
            {
                "schema_hash": schema_hash,
                "window": metadata,
                "labels": sorted(label_names),
                "feature_data_hash": feature_data_hash,
                "label_data_hash": label_data_hash,
            },
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        return "ds_" + hashlib.sha256(payload).hexdigest()[:16]

    @staticmethod
    def _frame_hash(frame: pd.DataFrame) -> str:
        row_hashes = pd.util.hash_pandas_object(frame, index=True).to_numpy()
        return hashlib.sha256(row_hashes.tobytes()).hexdigest()
