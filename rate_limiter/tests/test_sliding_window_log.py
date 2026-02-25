from datetime import datetime
from unittest.mock import patch

import pytest

from rate_limiter.strategies.sliding_window_log import SlidingWindowLogStrategy
from tests.conftest import make_mock_datetime

FIXED_TIME = datetime(2025, 1, 1)


class TestSlidingWindowLogStrategy:
    @pytest.fixture
    def mock_dt(self):
        return make_mock_datetime(FIXED_TIME)

    async def test_allows_requests_within_capacity(self, mock_dt):
        with patch("rate_limiter.strategies.sliding_window_log.datetime", mock_dt):
            strategy = SlidingWindowLogStrategy(capacity=3, window_size=10)
            for _ in range(3):
                assert await strategy.allow() is True

    async def test_denies_when_capacity_exhausted(self, mock_dt):
        with patch("rate_limiter.strategies.sliding_window_log.datetime", mock_dt):
            strategy = SlidingWindowLogStrategy(capacity=2, window_size=10)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_evicts_old_entries_allowing_new_requests(self, mock_dt):
        with patch("rate_limiter.strategies.sliding_window_log.datetime", mock_dt):
            strategy = SlidingWindowLogStrategy(capacity=2, window_size=5)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 6)
            assert await strategy.allow() is True

    async def test_partial_eviction(self, mock_dt):
        """Only entries older than window_size are evicted."""
        with patch("rate_limiter.strategies.sliding_window_log.datetime", mock_dt):
            strategy = SlidingWindowLogStrategy(capacity=3, window_size=10)
            assert await strategy.allow() is True  # t=0

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 6)
            assert await strategy.allow() is True  # t=6

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 8)
            assert await strategy.allow() is True  # t=8

            # t=11: entry at t=0 evicted, entries at t=6 and t=8 remain
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 11)
            assert await strategy.allow() is True  # 2 remaining + 1 new = 3 <= capacity
            assert await strategy.allow() is False  # 3 = capacity, denied

    async def test_zero_capacity_denies_everything(self, mock_dt):
        with patch("rate_limiter.strategies.sliding_window_log.datetime", mock_dt):
            strategy = SlidingWindowLogStrategy(capacity=0, window_size=10)
            assert await strategy.allow() is False

    async def test_no_boundary_burst(self, mock_dt):
        """Unlike Fixed Window, requests just before and after a boundary share the same sliding window."""
        with patch("rate_limiter.strategies.sliding_window_log.datetime", mock_dt):
            strategy = SlidingWindowLogStrategy(capacity=2, window_size=10)

            # t=9: two requests at end of "would-be" window
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 9)
            assert await strategy.allow() is True
            assert await strategy.allow() is True

            # t=11: only 2s later, the entries from t=9 are still within the 10s window
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 11)
            assert await strategy.allow() is False

    async def test_all_entries_expire(self, mock_dt):
        """After enough time, all entries are evicted and full capacity is available."""
        with patch("rate_limiter.strategies.sliding_window_log.datetime", mock_dt):
            strategy = SlidingWindowLogStrategy(capacity=2, window_size=5)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 1, 0)
            for _ in range(2):
                assert await strategy.allow() is True
            assert await strategy.allow() is False
