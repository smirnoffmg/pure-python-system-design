from datetime import datetime
from unittest.mock import patch

import pytest

from rate_limiter.strategies.sliding_window_counter import SlidingWindowCounterStrategy
from tests.conftest import make_mock_datetime

FIXED_TIME = datetime(2025, 1, 1)


class TestSlidingWindowCounterStrategy:
    @pytest.fixture
    def mock_dt(self):
        return make_mock_datetime(FIXED_TIME)

    async def test_allows_requests_within_capacity(self, mock_dt):
        with patch("rate_limiter.strategies.sliding_window_counter.datetime", mock_dt):
            strategy = SlidingWindowCounterStrategy(capacity=3, window_size=10)
            for _ in range(3):
                assert await strategy.allow() is True

    async def test_denies_when_capacity_exhausted(self, mock_dt):
        with patch("rate_limiter.strategies.sliding_window_counter.datetime", mock_dt):
            strategy = SlidingWindowCounterStrategy(capacity=2, window_size=10)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_window_rollover_carries_weighted_previous(self, mock_dt):
        """After rollover, previous window's count is weighted by overlap fraction."""
        with patch("rate_limiter.strategies.sliding_window_counter.datetime", mock_dt):
            strategy = SlidingWindowCounterStrategy(capacity=10, window_size=10)

            for _ in range(8):
                assert await strategy.allow() is True

            # t=12: 2s into the second window
            # weight = 1 - 2/10 = 0.8, base estimate = 8 * 0.8 = 6.4
            # Check is before increment, so:
            #   req1: 6.4+0=6.4 < 10 → allow (current→1)
            #   req2: 6.4+1=7.4 < 10 → allow (current→2)
            #   req3: 6.4+2=8.4 < 10 → allow (current→3)
            #   req4: 6.4+3=9.4 < 10 → allow (current→4)
            #   req5: 6.4+4=10.4 >= 10 → deny
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 12)
            for _ in range(4):
                assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_prevents_boundary_burst(self, mock_dt):
        """Unlike Fixed Window, cannot get 2x capacity across window boundary."""
        with patch("rate_limiter.strategies.sliding_window_counter.datetime", mock_dt):
            strategy = SlidingWindowCounterStrategy(capacity=5, window_size=10)

            # Fill to capacity at t=0
            for _ in range(5):
                assert await strategy.allow() is True
            assert await strategy.allow() is False

            # t=11: just after window boundary
            # weight = 1 - 1/10 = 0.9
            # estimated = 5 * 0.9 + 0 = 4.5, only 0 more allowed (4.5 + 1 = 5.5 >= 5? no, < means allow at 5.5? let me recalculate)
            # Actually: estimated < capacity means allow. 4.5 < 5 => allow, after increment current=1, next check: 5*0.9+1=5.5 >= 5 => deny
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 11)
            assert await strategy.allow() is True  # est=4.5 < 5
            assert await strategy.allow() is False  # est=5.5 >= 5

    async def test_zero_capacity_denies_everything(self, mock_dt):
        with patch("rate_limiter.strategies.sliding_window_counter.datetime", mock_dt):
            strategy = SlidingWindowCounterStrategy(capacity=0, window_size=10)
            assert await strategy.allow() is False

    async def test_full_previous_window_expires(self, mock_dt):
        """After a full window has passed, previous count has zero weight."""
        with patch("rate_limiter.strategies.sliding_window_counter.datetime", mock_dt):
            strategy = SlidingWindowCounterStrategy(capacity=2, window_size=10)

            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            # Move two full windows ahead — previous is completely expired
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 25)
            for _ in range(2):
                assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_weight_at_window_start(self, mock_dt):
        """At the very start of a new window, weight of previous is ~1.0."""
        with patch("rate_limiter.strategies.sliding_window_counter.datetime", mock_dt):
            strategy = SlidingWindowCounterStrategy(capacity=3, window_size=10)

            for _ in range(3):
                assert await strategy.allow() is True

            # t=10.001: just barely rolled over
            # weight ≈ 0.9999, estimate = 3 * 0.9999 + 0 ≈ 2.9997 < 3 → barely allows 1
            # next: 3 * 0.9999 + 1 ≈ 3.9997 >= 3 → deny
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 10, 1000)
            assert await strategy.allow() is True
            assert await strategy.allow() is False
