from datetime import datetime
from unittest.mock import patch

import pytest

from rate_limiter.strategies.leaky_bucket import LeakyBucketStrategy
from tests.conftest import make_mock_datetime

FIXED_TIME = datetime(2025, 1, 1)


class TestLeakyBucketStrategy:
    @pytest.fixture
    def mock_dt(self):
        return make_mock_datetime(FIXED_TIME)

    async def test_allows_requests_within_capacity(self, mock_dt):
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=3, rate=1)
            for _ in range(3):
                assert await strategy.allow() is True

    async def test_denies_when_bucket_full(self, mock_dt):
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=2, rate=1)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_drains_over_time_allowing_new_requests(self, mock_dt):
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=2, rate=1)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 1)
            assert await strategy.allow() is True

    async def test_drains_multiple_at_once(self, mock_dt):
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=3, rate=1)
            for _ in range(3):
                assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 2)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_does_not_drain_below_zero(self, mock_dt):
        """Water level should never go negative even with long elapsed time."""
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=2, rate=1)
            assert await strategy.allow() is True

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 1, 0)
            for _ in range(2):
                assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_zero_capacity_denies_everything(self, mock_dt):
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=0, rate=1)
            assert await strategy.allow() is False

    async def test_zero_rate_never_drains(self, mock_dt):
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=1, rate=0)
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 1, 0, 0)
            assert await strategy.allow() is False

    async def test_high_rate_drains_quickly(self, mock_dt):
        with patch("rate_limiter.strategies.leaky_bucket.datetime", mock_dt):
            strategy = LeakyBucketStrategy(capacity=5, rate=10)
            for _ in range(5):
                assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 0, 500_000)
            for _ in range(5):
                assert await strategy.allow() is True
            assert await strategy.allow() is False
