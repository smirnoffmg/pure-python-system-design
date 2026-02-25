# API Reference

## POST /shorten

Creates a short code for a URL.

**Request:**

```http
POST /shorten HTTP/1.1
Content-Type: application/json

{"url": "https://example.com/path"}
```

**Response (201 Created):**

```json
{"short_code": "1"}
```

**Errors:**

| Status | Reason                 |
| ------ | ---------------------- |
| 400    | Missing or invalid URL |
| 500    | Internal server error  |

## GET /{short_code}

Redirects to the original URL.

**Response (302 Found):**

```http
HTTP/1.1 302 Found
Location: https://example.com/path
```

**Errors:**

| Status | Reason               |
| ------ | -------------------- |
| 404    | Short code not found |

## GET /health

Health check endpoint.

**Response (200 OK):**

```json
{"status": "healthy", "service": "url_shortener"}
```
