"""
Domain layer - Core business logic and entities.
"""

from .encoder import Base62Encoder, BaseEncoder
from .exceptions import (
    EncodingError,
    StorageError,
    URLShortenerError,
    ValidationError,
)

__all__ = [
    "Base62Encoder",
    "BaseEncoder",
    "URLShortenerError",
    "ValidationError",
    "StorageError",
    "EncodingError",
]
