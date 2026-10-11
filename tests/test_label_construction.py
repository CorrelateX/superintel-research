import pandas as pd

from superintel_research.datasets.label_construction import LabelBuilder, LabelConfig


def test_forward_labels_are_net_of_explicit_costs_and_drop_unknown_future():
    frame = pd.DataFrame({"close": [100.0, 101.0, 103.0, 102.0, 104.0, 105.0]})
    builder = LabelBuilder(LabelConfig(horizon=2, fee_bps=2.0, slippage_bps=3.0))
    labels = builder.build(frame)

    assert len(labels) == len(frame) - 2
    assert (labels["round_trip_cost"] == 0.0005).all()
    assert labels["forward_return_net"].notna().all()


def test_label_builder_requires_close():
    try:
        LabelBuilder().build(pd.DataFrame({"open": [1.0, 2.0]}))
    except ValueError:
        pass
    else:
        raise AssertionError("missing close column must be rejected")
