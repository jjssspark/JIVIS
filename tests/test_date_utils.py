from datetime import datetime
from src.tools.date_utils import format_elapsed


def test_format_elapsed_returns_empty_when_none():
    assert format_elapsed(None) == ""


def test_format_elapsed_returns_empty_when_invalid_format():
    assert format_elapsed("garbled") == ""


def test_format_elapsed_returns_empty_under_one_minute():
    now = datetime(2026, 7, 19, 12, 0, 30)
    last_ts = "2026-07-19 12:00:00"
    assert format_elapsed(last_ts, now=now) == ""


def test_format_elapsed_returns_minutes_under_one_hour():
    now = datetime(2026, 7, 19, 12, 34, 0)
    last_ts = "2026-07-19 12:00:00"
    assert format_elapsed(last_ts, now=now) == "34분"


def test_format_elapsed_returns_hours_only_when_exact():
    now = datetime(2026, 7, 19, 15, 0, 0)
    last_ts = "2026-07-19 12:00:00"
    assert format_elapsed(last_ts, now=now) == "3시간"


def test_format_elapsed_returns_hours_and_minutes():
    now = datetime(2026, 7, 19, 15, 12, 0)
    last_ts = "2026-07-19 12:00:00"
    assert format_elapsed(last_ts, now=now) == "3시간 12분"
