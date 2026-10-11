from __future__ import annotations

from datetime import date
import pandas as pd
from superintel_research.calendar.exchange_calendar import ExchangeCalendar


def test_is_trading_day_weekend() -> None:
    cal = ExchangeCalendar()
    saturday = date(2024, 1, 6)
    sunday = date(2024, 1, 7)
    assert not cal.is_trading_day(saturday)
    assert not cal.is_trading_day(sunday)


def test_is_trading_day_holiday() -> None:
    cal = ExchangeCalendar()
    new_years = date(2024, 1, 1)  # NYSE Holiday
    assert not cal.is_trading_day(new_years, exchange="NYSE")

    regular_day = date(2024, 1, 2)  # Tuesday
    assert cal.is_trading_day(regular_day, exchange="NYSE")


def test_filter_trading_days() -> None:
    cal = ExchangeCalendar()
    dates = pd.date_range("2024-01-01", periods=7, freq="D", tz="UTC")
    df = pd.DataFrame({"event_time": dates, "close": range(100, 107)})

    filtered = cal.filter_trading_days(df, time_column="event_time", exchange="NYSE")
    # Jan 1 is holiday (Mon), Jan 6 & 7 are weekend. Should retain 4 trading days.
    assert len(filtered) == 4
