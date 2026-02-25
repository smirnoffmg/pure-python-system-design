# URL Shortener

Pure Python URL shortener service using `asyncio`.

[View Source on GitHub](https://github.com/smirnoffmg/pure-python-system-design/tree/main/url_shortener){ .md-button }

## Quick Start

### Running the Server

```bash
cd url_shortener
uv run python -m url_shortener
```

Or using Make:

```bash
make run
```

The server starts at `http://localhost:8000` by default.

### Testing the API

**Shorten a URL:**

```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/path"}'
```

Response:

```json
{"short_code": "1"}
```

**Redirect to original URL:**

```bash
curl -I http://localhost:8000/1
```

Response:

```
HTTP/1.1 302 Found
Location: https://example.com/very/long/path
```

**Health check:**

```bash
curl http://localhost:8000/health
```

Response:

```json
{"status": "healthy", "service": "url_shortener"}
```

## Constraints

- **Package Manager**: `uv` only
- **Testing**: pytest with coverage
- **Server**: Pure asyncio (no frameworks)
- **Code Quality**: Ruff + mypy (strict)
- **Python**: 3.12+
