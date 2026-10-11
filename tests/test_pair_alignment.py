import pandas as pd

from superintel_research.statistics.pair_alignment import align_pair_frames


def test_alignment_uses_event_time_not_array_position():
    t = pd.date_range("2024-01-01", periods=5, freq="D", tz="UTC")
    left = pd.DataFrame({"event_time": [t[0], t[1], t[3], t[4]], "close": [10, 11, 13, 14]})
    right = pd.DataFrame({"event_time": [t[0], t[2], t[3], t[4]], "close": [20, 22, 23, 24]})

    aligned = align_pair_frames(left, right, "LEFT", "RIGHT")

    assert list(aligned.event_time) == [t[0], t[3], t[4]]
    assert aligned.x_prices.tolist() == [10.0, 13.0, 14.0]
    assert aligned.y_prices.tolist() == [20.0, 23.0, 24.0]


def test_duplicate_timestamp_is_last_write_wins():
    t = pd.Timestamp("2024-01-01", tz="UTC")
    left = pd.DataFrame(
        {
            "event_time": [t, t],
            "created_at": [pd.Timestamp("2024-01-02", tz="UTC"), pd.Timestamp("2024-01-03", tz="UTC")],
            "close": [10, 11],
        }
    )
    right = pd.DataFrame({"event_time": [t], "close": [20]})

    aligned = align_pair_frames(left, right, "LEFT", "RIGHT", min_observations=1)
    assert aligned.x_prices.tolist() == [11.0]
