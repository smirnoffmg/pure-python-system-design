"""
Concurrency Limiter Strategy
==============================

Unlike time-based strategies, this limits how many requests are
in-flight simultaneously rather than how many arrive per window.
Useful for protecting downstream services from being overwhelmed
by concurrent load regardless of arrival rate.

Algorithm:
    1. Maintain a counter of currently active (in-flight) requests.
    2. On allow(): if active < max_concurrent, increment and allow.
    3. The caller MUST signal completion (via release()) when the
       request finishes, so the counter is decremented.

Parameters:
    max_concurrent -- maximum number of simultaneous in-flight requests

Interface note:
    This strategy requires a release() call after each allowed request
    completes. A context-manager pattern is natural here:

        async with limiter.acquire():
            await handle_request()

Trade-offs:
    + Directly prevents overload — caps actual parallel work.
    + No time tracking or memory proportional to request volume.
    - Requires caller cooperation to release — a missed release leaks
      a slot permanently (timeout-based auto-release can mitigate this).
    - Does not limit request rate — 1000 fast sequential requests per
      second all pass if each finishes before the next starts.

Example:
    strategy = ConcurrencyLimiterStrategy(max_concurrent=50)
    if await strategy.allow():
        try:
            await handle(request)
        finally:
            await strategy.release()
"""

raise NotImplementedError
