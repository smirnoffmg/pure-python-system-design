"""
Sanic integration — rate-limit middleware using client IP.

    pip install sanic rate-limiter
    sanic examples.sanic_example:app
"""

from sanic import Sanic, json
from sanic.request import Request
from sanic.response import text

from rate_limiter import RateLimiter, TokenBucketStrategy

app = Sanic("RateLimitedApp")
limiter = RateLimiter(lambda: TokenBucketStrategy(capacity=10, rate=2))


@app.middleware("request")
async def rate_limit_middleware(request: Request):
    key = request.remote_addr or request.ip or "unknown"
    if not await limiter.allow(key):
        return text("Rate limit exceeded", status=429)


@app.get("/")
async def index(request: Request):
    return json({"message": "Hello, World!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
