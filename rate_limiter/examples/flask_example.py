"""
Flask integration — rate-limit decorator using client IP.

Flask is synchronous, so we run the async limiter via asyncio.run().

    pip install flask rate-limiter
    flask --app examples.flask_example run
"""

import asyncio
from functools import wraps

from flask import Flask, abort, jsonify, request

from rate_limiter import RateLimiter, TokenBucketStrategy

app = Flask(__name__)
limiter = RateLimiter(lambda: TokenBucketStrategy(capacity=10, rate=2))


def rate_limit(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.remote_addr or "unknown"
        if not asyncio.run(limiter.allow(key)):
            abort(429, description="Rate limit exceeded")
        return f(*args, **kwargs)

    return wrapper


@app.get("/")
@rate_limit
def index():
    return jsonify(message="Hello, World!")


if __name__ == "__main__":
    app.run(port=8080)
