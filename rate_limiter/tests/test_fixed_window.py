from datetime import datetime
from unittest.mock import patch

import pytest

from rate_limiter.strategies.fixed_window import FixedWindowStrategy
from tests.conftest import make_mock_datetime

FIXED_TIME = datetime(2025, 1, 1)


class TestFixedWindowStrategy:
    @pytest.fixture
    def mock_dt(self):
        return make_mock_datetime(FIXED_TIME)

    async def test_allows_requests_within_window(self, mock_dt):
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            strategy = FixedWindowStrategy(capacity=3, window_size=10)
            for _ in range(3):
                assert await strategy.allow() is True

    async def test_denies_when_window_capacity_exhausted(self, mock_dt):
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            strategy = FixedWindowStrategy(capacity=2, window_size=10)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_resets_after_window_expires(self, mock_dt):
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            strategy = FixedWindowStrategy(capacity=1, window_size=5)
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 6)
            assert await strategy.allow() is True

    async def test_does_not_reset_before_window_expires(self, mock_dt):
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            strategy = FixedWindowStrategy(capacity=1, window_size=10)
            assert await strategy.allow() is True

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 9)
            assert await strategy.allow() is False

    async def test_zero_capacity_denies_everything(self, mock_dt):
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            strategy = FixedWindowStrategy(capacity=0, window_size=10)
            assert await strategy.allow() is False

    async def test_multiple_window_rollovers(self, mock_dt):
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            strategy = FixedWindowStrategy(capacity=1, window_size=5)

            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 6)
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 12)
            assert await strategy.allow() is True

    async def test_window_boundary_exact(self, mock_dt):
        """At exactly the window boundary, window should NOT reset (> not >=)."""
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            strategy = FixedWindowStrategy(capacity=1, window_size=5)
            assert await strategy.allow() is True

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 5)
            assert await strategy.allow() is False
