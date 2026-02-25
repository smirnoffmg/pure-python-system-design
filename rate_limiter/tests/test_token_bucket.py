from datetime import datetime
from unittest.mock import patch

import pytest

from rate_limiter.strategies.token_bucket import TokenBucketStrategy
from tests.conftest import make_mock_datetime

FIXED_TIME = datetime(2025, 1, 1)


class TestTokenBucketStrategy:
    @pytest.fixture
    def mock_dt(self):
        return make_mock_datetime(FIXED_TIME)

    async def test_allows_requests_within_capacity(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            strategy = TokenBucketStrategy(capacity=5, rate=1)

        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            for _ in range(5):
                assert await strategy.allow() is True

    async def test_denies_when_capacity_exhausted(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            strategy = TokenBucketStrategy(capacity=2, rate=1)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_refills_tokens_after_time_passes(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            strategy = TokenBucketStrategy(capacity=2, rate=1)
            assert await strategy.allow() is True
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 3)
            assert await strategy.allow() is True

    async def test_refill_does_not_exceed_max_capacity(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            strategy = TokenBucketStrategy(capacity=3, rate=10)
            assert await strategy.allow() is True

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 1, 0)

            for _ in range(3):
                assert await strategy.allow() is True
            assert await strategy.allow() is False

    async def test_zero_capacity_denies_everything(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            strategy = TokenBucketStrategy(capacity=0, rate=10)
            assert await strategy.allow() is False

    async def test_zero_rate_never_refills(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            strategy = TokenBucketStrategy(capacity=1, rate=0)
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 1, 0, 0)
            assert await strategy.allow() is False

    async def test_fractional_seconds_refill(self, mock_dt):
        """Ensure total_seconds() handles sub-second precision correctly."""
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            strategy = TokenBucketStrategy(capacity=1, rate=2)
            assert await strategy.allow() is True
            assert await strategy.allow() is False

            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 0, 500_000)
            assert await strategy.allow() is True
