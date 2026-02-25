from datetime import datetime
from unittest.mock import patch

import pytest

from rate_limiter.rate_limiter import RateLimiter
from rate_limiter.strategies.token_bucket import TokenBucketStrategy
from rate_limiter.strategies.fixed_window import FixedWindowStrategy
from tests.conftest import make_mock_datetime

FIXED_TIME = datetime(2025, 1, 1)


class TestRateLimiter:
    @pytest.fixture
    def mock_dt(self):
        return make_mock_datetime(FIXED_TIME)

    async def test_tracks_separate_keys_independently(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            limiter = RateLimiter(lambda: TokenBucketStrategy(capacity=1, rate=0))

            assert await limiter.allow("client-a") is True
            assert await limiter.allow("client-a") is False

            assert await limiter.allow("client-b") is True
            assert await limiter.allow("client-b") is False

    async def test_same_key_shares_bucket(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            limiter = RateLimiter(lambda: TokenBucketStrategy(capacity=2, rate=0))

            assert await limiter.allow("client-a") is True
            assert await limiter.allow("client-a") is True
            assert await limiter.allow("client-a") is False

    async def test_works_with_different_strategies(self, mock_dt):
        with patch("rate_limiter.strategies.fixed_window.datetime", mock_dt):
            limiter = RateLimiter(
                lambda: FixedWindowStrategy(capacity=1, window_size=10)
            )

            assert await limiter.allow("x") is True
            assert await limiter.allow("x") is False

    async def test_lazily_creates_buckets(self, mock_dt):
        call_count = 0

        def counting_factory():
            nonlocal call_count
            call_count += 1
            return TokenBucketStrategy(capacity=5, rate=1)

        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            limiter = RateLimiter(counting_factory)
            assert call_count == 0

            await limiter.allow("a")
            assert call_count == 1

            await limiter.allow("a")
            assert call_count == 1

            await limiter.allow("b")
            assert call_count == 2

    async def test_many_keys(self, mock_dt):
        with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
            limiter = RateLimiter(lambda: TokenBucketStrategy(capacity=1, rate=0))

            for i in range(100):
                assert await limiter.allow(f"client-{i}") is True
                assert await limiter.allow(f"client-{i}") is False
