from rate_limiter.strategies.concurrency_limiter import ConcurrencyLimiterStrategy


class TestConcurrencyLimiterStrategy:
    async def test_allows_within_max_concurrent(self):
        strategy = ConcurrencyLimiterStrategy(max_concurrent=3)
        for _ in range(3):
            assert await strategy.allow() is True

    async def test_denies_when_at_max_concurrent(self):
        strategy = ConcurrencyLimiterStrategy(max_concurrent=2)
        assert await strategy.allow() is True
        assert await strategy.allow() is True
        assert await strategy.allow() is False

    async def test_release_frees_slot(self):
        strategy = ConcurrencyLimiterStrategy(max_concurrent=1)
        assert await strategy.allow() is True
        assert await strategy.allow() is False

        await strategy.release()
        assert await strategy.allow() is True

    async def test_multiple_release_cycles(self):
        strategy = ConcurrencyLimiterStrategy(max_concurrent=2)
        assert await strategy.allow() is True
        assert await strategy.allow() is True
        assert await strategy.allow() is False

        await strategy.release()
        assert await strategy.allow() is True
        assert await strategy.allow() is False

        await strategy.release()
        await strategy.release()
        assert await strategy.allow() is True
        assert await strategy.allow() is True
        assert await strategy.allow() is False

    async def test_zero_max_concurrent_denies_everything(self):
        strategy = ConcurrencyLimiterStrategy(max_concurrent=0)
        assert await strategy.allow() is False

    async def test_release_does_not_go_below_zero(self):
        strategy = ConcurrencyLimiterStrategy(max_concurrent=1)
        # Release without any allow — should not break
        await strategy.release()
        await strategy.release()

        # Should still respect max_concurrent=1
        assert await strategy.allow() is True
        assert await strategy.allow() is False

    async def test_high_concurrency(self):
        strategy = ConcurrencyLimiterStrategy(max_concurrent=100)
        for _ in range(100):
            assert await strategy.allow() is True
        assert await strategy.allow() is False

        for _ in range(50):
            await strategy.release()

        for _ in range(50):
            assert await strategy.allow() is True
        assert await strategy.allow() is False
