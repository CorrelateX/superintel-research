import pandas as pd

from superintel_research.datasets.assembler import DatasetAssembler


def test_dataset_snapshot_is_deterministic_for_identical_inputs():
    index = pd.date_range("2024-01-01", periods=4, freq="D", tz="UTC")
    features = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [4.0, 3.0, 2.0, 1.0]}, index=index)
    labels = pd.DataFrame({"target": [0, 1, 1, 0]}, index=index)

    assembler = DatasetAssembler()
    first = assembler.assemble(features, labels, {"window": "demo"})
    second = assembler.assemble(features, labels, {"window": "demo"})

    assert first.snapshot_id == second.snapshot_id
    assert first.feature_schema_hash == second.feature_schema_hash
    assert first.row_count == 4


def test_dataset_snapshot_changes_when_data_changes():
    index = pd.date_range("2024-01-01", periods=2, freq="D", tz="UTC")
    labels = pd.DataFrame({"target": [0, 1]}, index=index)
    assembler = DatasetAssembler()

    first = assembler.assemble(pd.DataFrame({"a": [1.0, 2.0]}, index=index), labels)
    second = assembler.assemble(pd.DataFrame({"a": [1.0, 3.0]}, index=index), labels)

    assert first.snapshot_id != second.snapshot_id
