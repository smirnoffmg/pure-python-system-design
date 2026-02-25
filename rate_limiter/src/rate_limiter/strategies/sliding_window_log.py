"""
Sliding Window Log Strategy
============================

Tracks the exact timestamp of every request within the current window.
On each new request, timestamps older than the window are discarded,
and the request is allowed only if the remaining count is below capacity.

Algorithm:
    1. Remove all entries older than (now - window_size) from the log.
    2. If len(log) < capacity, append now to the log and allow.
    3. Otherwise, deny.

Parameters:
    capacity    -- maximum number of requests allowed per window
    window_size -- window duration in seconds

Trade-offs:
    + Perfectly accurate — no boundary approximation errors.
    + Smooth rate enforcement — no burst at window edges.
    - Memory grows linearly with request volume (one timestamp per request).
    - Cleanup cost on each request is O(n) in the worst case for the
      expired entries, though amortised cost is low with a deque.

Comparison to Fixed Window:
    Fixed Window resets its counter at discrete boundaries, which allows
    up to 2x the intended rate at the boundary (e.g. capacity burst at
    the end of one window + capacity burst at the start of the next).
    Sliding Window Log eliminates this entirely.

Example:
    strategy = SlidingWindowLogStrategy(capacity=100, window_size=60)
    await strategy.allow()  # True if <100 requests in the last 60s
"""

raise NotImplementedError
