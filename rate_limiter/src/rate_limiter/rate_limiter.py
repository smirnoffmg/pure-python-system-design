from collections.abc import Callable

from rate_limiter.protocols import IStrategy


class RateLimiter:
    """Per-key rate limiter that lazily creates a strategy instance per key."""

    def __init__(self, strategy_factory: Callable[[], IStrategy]):
        self._strategy_factory = strategy_factory
        self._buckets: dict[str, IStrategy] = {}

    async def allow(self, key: str) -> bool:
        if key not in self._buckets:
            self._buckets[key] = self._strategy_factory()
        return await self._buckets[key].allow()
