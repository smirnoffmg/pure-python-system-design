"""
Token Bucket Strategy
======================

Starts with a bucket full of tokens (up to capacity). Each allowed
request consumes one token. Tokens are replenished at a fixed rate
over time, up to the maximum capacity.

Algorithm:
    1. Compute elapsed time since the last check.
    2. Add elapsed * rate tokens to the bucket (capped at capacity).
    3. If tokens >= 1, consume one token and allow.
    4. Otherwise, deny.

Parameters:
    capacity -- maximum number of tokens the bucket can hold;
                also the burst size (max requests allowed at once)
    rate     -- tokens added per second

Trade-offs:
    + Allows controlled bursts up to capacity while enforcing a
      long-term average rate.
    + O(1) time and memory per request — just arithmetic.
    + Smooth refill — no sudden counter resets like Fixed Window.
    - Burst size and refill rate are separate knobs that must be
      tuned together; misconfiguration can allow unwanted spikes.

Comparison to Leaky Bucket:
    Token Bucket permits bursts (spend all tokens at once), while
    Leaky Bucket enforces a steady drain rate and absorbs bursts
    into the queue. Token Bucket is more permissive for bursty
    workloads; Leaky Bucket is better for smoothing output rate.

Example:
    strategy = TokenBucketStrategy(capacity=10, rate=2)
    await strategy.allow()  # True if tokens available
"""

import asyncio
from datetime import datetime


class TokenBucketStrategy:
    def __init__(self, capacity: int, rate: int):
        self._max_capacity = capacity
        self._current_capacity: float = capacity
        self._rate = rate
        self._lock = asyncio.Lock()
        self._last_tick = datetime.now()

    def _refill(self) -> None:
        now = datetime.now()
        elapsed = (now - self._last_tick).total_seconds()
        self._last_tick = now
        self._current_capacity = min(
            self._max_capacity,
            self._current_capacity + elapsed * self._rate,
        )

    async def allow(self, *args, **kwargs) -> bool:
        async with self._lock:
            self._refill()

            if self._current_capacity >= 1:
                self._current_capacity -= 1
                return True

            return False
