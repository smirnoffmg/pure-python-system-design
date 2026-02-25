"""
Sliding Window Counter Strategy
=================================

A hybrid of Fixed Window and Sliding Window Log. Maintains request
counts for the current and previous fixed windows, then estimates
the effective count using a weighted average based on how far into
the current window the request arrives.

Algorithm:
    1. Determine which fixed window "now" falls into.
    2. If the window has rolled over, rotate: previous = current, current = 0.
    3. Compute the overlap fraction of the previous window:
           weight = 1 - (elapsed_in_current_window / window_size)
    4. Estimated count = previous_count * weight + current_count.
    5. If estimated count < capacity, increment current_count and allow.
    6. Otherwise, deny.

Parameters:
    capacity    -- maximum number of requests allowed per window
    window_size -- window duration in seconds

Trade-offs:
    + Near the accuracy of Sliding Window Log without storing individual
      timestamps — memory is O(1) (two counters + two timestamps).
    + Smooths out the boundary-burst problem of Fixed Window.
    - The count is an estimate, not exact. Under adversarial timing it
      can be slightly off, but in practice the error is negligible.

Comparison to Sliding Window Log:
    Sliding Window Log stores every timestamp (O(n) memory) for perfect
    accuracy. Sliding Window Counter trades a tiny accuracy loss for
    constant memory — just two integers and a timestamp.

Comparison to Fixed Window:
    Fixed Window allows up to 2x capacity at the boundary between two
    windows. The weighted average here prevents that spike.

Example:
    strategy = SlidingWindowCounterStrategy(capacity=100, window_size=60)
    await strategy.allow()  # True if estimated rate < 100 req/60s
"""

import asyncio
from datetime import datetime, timedelta


class SlidingWindowCounterStrategy:
    def __init__(self, capacity: int, window_size: int):
        self._capacity = capacity
        self._window_size = window_size
        self._current_count = 0
        self._previous_count = 0
        self._window_start = datetime.now()
        self._lock = asyncio.Lock()

    def _rotate(self, now: datetime) -> None:
        elapsed = (now - self._window_start).total_seconds()

        if elapsed >= 2 * self._window_size:
            self._previous_count = 0
            self._current_count = 0
            self._window_start = now
        elif elapsed >= self._window_size:
            self._previous_count = self._current_count
            self._current_count = 0
            self._window_start = self._window_start + timedelta(
                seconds=self._window_size
            )

    def _estimate(self, now: datetime) -> float:
        elapsed_in_window = (now - self._window_start).total_seconds()
        weight = 1.0 - (elapsed_in_window / self._window_size)
        return self._previous_count * weight + self._current_count

    async def allow(self, *args, **kwargs) -> bool:
        async with self._lock:
            now = datetime.now()
            self._rotate(now)

            if self._estimate(now) < self._capacity:
                self._current_count += 1
                return True

            return False
