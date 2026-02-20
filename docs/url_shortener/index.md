# URL Shortener

Pure Python URL shortener service using `asyncio`.

## Architecture

- **HTTP API**: `asyncio` server with `asyncio.Protocol` implementation
- **Service**: `ShortenerService` (business logic)
- **Storage**: `InMemoryStorage` and `SQLiteStorage`
- **Encoder**: `Base62Encoder`

```mermaid
graph TB
    subgraph "Presentation Layer"
        HTTP[HTTP Protocol]
        Handler[Request Handler]
        Registry[Handler Registry]
    end
    
    subgraph "Application Layer"
        Service[Shortener Service]
        BaseService[Base Shortener]
    end
    
    subgraph "Domain Layer"
        Encoder[Base62 Encoder]
        Exceptions[Business Exceptions]
    end
    
    subgraph "Infrastructure Layer"
        Storage[Storage Implementations]
        HTTPUtils[HTTP Utils]
        Config[Configuration]
        Factory[Factory Functions]
    end
    
    HTTP --> Handler
    Handler --> Registry
    Registry --> Service
    Service --> BaseService
    BaseService --> Storage
    Service --> Encoder
    Service --> Exceptions
    Storage --> Factory
    HTTPUtils --> Factory
    Config --> Factory
    Factory --> Service
```

## Constraints

- **Package Manager**: `uv` only
- **Testing**: pytest suite with httpx
- **Server**: Pure asyncio (no frameworks)
- **Code Quality**: Ruff + mypy
- **Python**: 3.12+

## API

- `POST /shorten` - Create short URL (returns "http://domain/short_code")
- `GET /<short_code>` - Redirect to long URL (returns 302) or 404 if not found
- `GET /health` - Health check endpoint

## Race Conditions

The URL shortener handles several potential race conditions:

### Concurrent URL Shortening

- Multiple requests to shorten the same URL are handled safely
- The storage layer ensures atomic operations for saving mappings
- If two requests try to shorten the same URL, they'll get the same short code

### Storage Operations

- All storage operations (save, get, delete) are atomic
- The InMemoryStorage uses `asyncio.Lock` to synchronize access
- The SQLiteStorage uses transactions for consistency
