# Testing

## Running Tests

```bash
cd rate_limiter
uv run pytest
```

## Test Structure

```
rate_limiter/tests/
├── conftest.py              # make_mock_datetime helper
├── test_rate_limiter.py     # RateLimiter per-key behaviour
├── test_token_bucket.py     # TokenBucketStrategy
├── test_fixed_window.py     # FixedWindowStrategy
└── test_leaky_bucket.py     # LeakyBucketStrategy
```

### Time Control

All strategies depend on `datetime.now()`. Tests use a shared `make_mock_datetime` helper (in `conftest.py`) that returns a mock whose `.now()` you can advance to any point in time:

```python
mock_dt = make_mock_datetime(datetime(2025, 1, 1))

with patch("rate_limiter.strategies.token_bucket.datetime", mock_dt):
    strategy = TokenBucketStrategy(capacity=2, rate=1)
    assert await strategy.allow() is True
    assert await strategy.allow() is True
    assert await strategy.allow() is False

    mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 3)
    assert await strategy.allow() is True  # refilled after 3s
```

This avoids `asyncio.sleep` in tests — time is deterministic.

## Constraints

- **Dependencies**: None at runtime; `pytest` + `pytest-asyncio` for tests
- **Async mode**: `asyncio_mode = "auto"` (no need for `@pytest.mark.asyncio`)
- **Python**: 3.12+
