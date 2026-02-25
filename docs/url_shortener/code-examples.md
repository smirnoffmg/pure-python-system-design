# Code Examples

## Base62 Encoder

The encoder converts sequential IDs to short, URL-safe strings:

```python
from url_shortener.domain import Base62Encoder

encoder = Base62Encoder()

# Encode integers to short codes
encoder.encode(1)      # "1"
encoder.encode(62)     # "10"
encoder.encode(1000)   # "g8"

# Decode back to integers
encoder.decode("g8")   # 1000
```

## Storage Backends

**In-Memory Storage** (default, fast, non-persistent):

```python
from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure import InMemoryStorage

encoder = Base62Encoder()
storage = InMemoryStorage(encoder)

# Create short code
short_code = await storage.create_short_code("https://example.com")

# Retrieve original URL
url = await storage.get_full_url(short_code)
```

**SQLite Storage** (persistent):

```python
from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure import SQLiteStorage

encoder = Base62Encoder()
storage = SQLiteStorage(encoder, db_path="./urls.db")

# Same interface as InMemoryStorage
short_code = await storage.create_short_code("https://example.com")
```

## Using the Factory

The recommended way to create a configured shortener:

```python
from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure.config import Config
from url_shortener.infrastructure.factory import create_shortener

config = Config.from_env()
encoder = Base62Encoder()
shortener = create_shortener(config, encoder)

# Use the shortener
short_code = await shortener.create_short_code("https://example.com")
original = await shortener.get_full_url(short_code)
```
