import pandas as pd

from superintel_research.datasets.temporal_split import WalkForwardSplitter


def test_walk_forward_has_explicit_purge_gap():
    frame = pd.DataFrame({"x": range(30)})
    splitter = WalkForwardSplitter(train_size=10, test_size=5, step_size=5, purge_gap=2)
    folds = splitter.split(frame)

    assert len(folds) == 3
    assert folds[0].train_start == 0
    assert folds[0].train_end == 10
    assert folds[0].test_start == 12
    assert folds[0].test_end == 17
    assert all(fold.purge_size == 2 for fold in folds)


def test_invalid_window_sizes_fail_closed():
    try:
        WalkForwardSplitter(train_size=0, test_size=5)
    except ValueError:
        pass
    else:
        raise AssertionError("zero train_size must be rejected")
