"""
URL Shortener - A simple URL shortening service.

This package provides a clean, layered architecture for URL shortening functionality.
"""

# Domain layer - Core business logic
# Application layer - Use cases and services
from .application import BaseShortener, Shortener
from .domain import (
    Base62Encoder,
    BaseEncoder,
    EncodingError,
    StorageError,
    URLShortenerError,
    ValidationError,
)

# Infrastructure layer - External concerns
from .infrastructure import (
    BaseStorage,
    DatabaseManager,
    HTTPError,
    HTTPRequest,
    HTTPRequestParser,
    HTTPResponse,
    HTTPResponseSerializer,
    InMemoryStorage,
    SQLiteStorage,
    extract_domain,
    get_logger,
    is_valid_url,
    normalize_url,
)

# Presentation layer - HTTP handlers and API
from .presentation import (
    HandlerRegistry,
    HTTPProtocol,
    RequestHandler,
    error_response,
    handle_redirect,
    handle_shorten,
    json_response,
    not_found,
    redirect_response,
    serve,
)

__all__ = [
    # Domain
    "Base62Encoder",
    "BaseEncoder",
    "URLShortenerError",
    "ValidationError",
    "StorageError",
    "EncodingError",
    # Application
    "BaseShortener",
    "Shortener",
    # Infrastructure
    "BaseStorage",
    "InMemoryStorage",
    "SQLiteStorage",
    "DatabaseManager",
    "HTTPRequestParser",
    "HTTPResponseSerializer",
    "HTTPRequest",
    "HTTPResponse",
    "HTTPError",
    "is_valid_url",
    "normalize_url",
    "extract_domain",
    "get_logger",
    # Presentation
    "HTTPProtocol",
    "RequestHandler",
    "serve",
    "HandlerRegistry",
    "handle_shorten",
    "handle_redirect",
    "json_response",
    "error_response",
    "redirect_response",
    "not_found",
]
