# Testing

## Running Tests

```bash
cd url_shortener

# Run all tests
make test

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run benchmarks
make benchmark
```

## Race Condition Handling

### Concurrent URL Shortening

The storage layer handles concurrent requests safely:

```python
# InMemoryStorage uses asyncio.Lock
async with self.lock:
    if full_url in self.full_x_short:
        return self.full_x_short[full_url]  # Return existing
    # ... create new mapping
```

- Multiple requests for the same URL return the same short code
- Atomic operations prevent duplicate entries

### SQLite Transactions

SQLite storage uses transactions for consistency:

```python
with self.db_manager.get_connection() as conn:
    cursor = conn.execute("SELECT id FROM url_mapping WHERE full_url = ?", (url,))
    row = cursor.fetchone()
    if row:
        return self.encoder.encode(row[0])
    # ... insert if not exists
    conn.commit()
```
