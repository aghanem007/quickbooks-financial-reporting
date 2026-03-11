import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from main import resolve_period


def _mock_datetime(fixed_now):
    """Return a mock datetime class whose .now() returns fixed_now."""
    mock_dt = MagicMock(wraps=datetime)
    mock_dt.now.return_value = fixed_now
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    return mock_dt


class TestResolvePeriod:
    @patch("main.datetime")
    def test_monthly_returns_previous_month(self, mock_dt):
        # "Today" is March 15 2025 → previous month is Feb 2025
        mock_dt.now.return_value = datetime(2025, 3, 15)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        start, end = resolve_period("monthly")
        assert start == "2025-02-01"
        assert end == "2025-02-28"

    @patch("main.datetime")
    def test_monthly_january_wraps_to_december(self, mock_dt):
        # "Today" is Jan 10 2025 → previous month is Dec 2024
        mock_dt.now.return_value = datetime(2025, 1, 10)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        start, end = resolve_period("monthly")
        assert start == "2024-12-01"
        assert end == "2024-12-31"

    @patch("main.datetime")
    def test_quarterly_returns_previous_quarter(self, mock_dt):
        # "Today" is May 20 2025 (Q2) → previous quarter is Q1 (Jan-Mar)
        mock_dt.now.return_value = datetime(2025, 5, 20)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        start, end = resolve_period("quarterly")
        assert start == "2025-01-01"
        assert end == "2025-03-31"

    @patch("main.datetime")
    def test_quarterly_q1_wraps_to_previous_year(self, mock_dt):
        # "Today" is Feb 15 2025 (Q1) → previous quarter is Q4 2024
        mock_dt.now.return_value = datetime(2025, 2, 15)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        start, end = resolve_period("quarterly")
        assert start == "2024-10-01"
        assert end == "2024-12-31"

    @patch("main.datetime")
    def test_yearly_returns_jan1_to_today(self, mock_dt):
        mock_dt.now.return_value = datetime(2025, 6, 30)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        start, end = resolve_period("yearly")
        assert start == "2025-01-01"
        assert end == "2025-06-30"
