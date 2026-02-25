"""
Fixed Window Strategy
======================

Divides time into fixed-size windows and counts requests within
each window. When a new window begins, the counter resets to zero.

Algorithm:
    1. Compute elapsed time since the current window started.
    2. If elapsed > window_size, reset the counter and start a
       new window.
    3. If count < capacity, increment the counter and allow.
    4. Otherwise, deny.

Parameters:
    capacity    -- maximum number of requests allowed per window
    window_size -- window duration in seconds

Trade-offs:
    + Simplest to understand and implement — one counter, one
      timestamp.
    + O(1) time and memory per request.
    - Boundary burst problem: a client can send capacity requests
      at the end of one window and capacity more at the start of
      the next, achieving 2x the intended rate across the boundary.
    - Counter resets abruptly, which can cause traffic spikes at
      window transitions.

Comparison to Sliding Window Counter:
    Sliding Window Counter smooths the boundary problem by weighting
    the previous window's count, at the cost of a slightly more
    complex calculation. Fixed Window is appropriate when simplicity
    matters and the boundary burst is acceptable.

Example:
    strategy = FixedWindowStrategy(capacity=100, window_size=60)
    await strategy.allow()  # True if <100 requests in current 60s window
"""

import asyncio
from datetime import datetime


class FixedWindowStrategy:
    def __init__(self, capacity: int, window_size: int):
        self._capacity = capacity
        self._window_size = window_size
        self._count = 0
        self._window_start = datetime.now()
        self._lock = asyncio.Lock()

    async def allow(self, *args, **kwargs) -> bool:
        async with self._lock:
            now = datetime.now()

            if (now - self._window_start).total_seconds() > self._window_size:
                self._window_start = now
                self._count = 0

            if self._count < self._capacity:
                self._count += 1
                return True

            return False
