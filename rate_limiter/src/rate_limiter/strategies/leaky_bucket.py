"""
Leaky Bucket Strategy
======================

Incoming requests fill the bucket. The bucket drains (leaks) at a
constant rate over time. If the bucket is full when a new request
arrives, the request is denied.

Algorithm:
    1. Compute elapsed time since the last check.
    2. Drain: subtract elapsed * rate from the water level (min 0).
    3. If water_level < capacity, increment water level and allow.
    4. Otherwise, deny.

Parameters:
    capacity -- maximum number of requests the bucket can hold
    rate     -- requests drained per second

Trade-offs:
    + Enforces a smooth, steady output rate regardless of input
      burstiness — ideal for protecting downstream services.
    + O(1) time and memory per request.
    - Does not permit bursts at all; even legitimate traffic spikes
      are rejected once the bucket is full.
    - A sustained burst fills the bucket instantly, and recovery
      depends entirely on the drain rate.

Comparison to Token Bucket:
    Token Bucket allows bursts up to capacity (spend accumulated
    tokens at once). Leaky Bucket absorbs bursts and enforces a
    uniform drain rate. Choose Leaky Bucket when you need strict
    output smoothing; choose Token Bucket when bursts are acceptable.

Example:
    strategy = LeakyBucketStrategy(capacity=10, rate=2)
    await strategy.allow()  # True if bucket has room
"""

import asyncio
from datetime import datetime


class LeakyBucketStrategy:
    def __init__(self, capacity: int, rate: int):
        self._capacity = capacity
        self._rate = rate
        self._water_level: float = 0
        self._last_tick = datetime.now()
        self._lock = asyncio.Lock()

    def _drain(self) -> None:
        now = datetime.now()
        elapsed = (now - self._last_tick).total_seconds()
        self._last_tick = now
        self._water_level = max(0, self._water_level - elapsed * self._rate)

    async def allow(self, *args, **kwargs) -> bool:
        async with self._lock:
            self._drain()

            if self._water_level < self._capacity:
                self._water_level += 1
                return True

            return False
