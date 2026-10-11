from __future__ import annotations

from datetime import datetime, timezone

import pytest

from superintel_research.storage.timescale import TimescaleMarketDataStore


class _FakeCursor:
    def __init__(self) -> None:
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params) -> None:
        assert "research.market_bars" in query
        self.params = params

    def fetchall(self):
        return [
            (
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                "SYNTH_A",
                100.0,
                101.0,
                99.0,
                100.5,
                10_000.0,
            )
        ]


class _FakeConnection:
    def __init__(self) -> None:
        self.fake_cursor = _FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.fake_cursor


def test_load_bars_maps_rows_to_public_contract(monkeypatch) -> None:
    connection = _FakeConnection()
    monkeypatch.setattr(
        TimescaleMarketDataStore,
        "_connect",
        staticmethod(lambda dsn: connection),
    )
    store = TimescaleMarketDataStore("postgresql://example")

    frame = store.load_bars(
        ["SYNTH_A"],
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end=datetime(2024, 2, 1, tzinfo=timezone.utc),
    )

    assert frame.columns.tolist() == [
        "event_time",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert frame.iloc[0]["symbol"] == "SYNTH_A"
    assert frame.iloc[0]["close"] == pytest.approx(100.5)
    assert str(frame["event_time"].dt.tz) == "UTC"


def test_load_bars_rejects_invalid_query_bounds() -> None:
    store = TimescaleMarketDataStore("postgresql://example")
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="symbols"):
        store.load_bars([], start=now, end=datetime(2024, 2, 1, tzinfo=timezone.utc))

    with pytest.raises(ValueError, match="start"):
        store.load_bars(["SYNTH_A"], start=now, end=now)
