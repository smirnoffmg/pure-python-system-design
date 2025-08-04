"""
Custom exceptions for the URL shortener service.
"""


class URLShortenerError(Exception):
    """Base exception for URL shortener service."""

    pass


class ValidationError(URLShortenerError):
    """Raised when input validation fails."""

    pass


class StorageError(URLShortenerError):
    """Raised when storage operations fail."""

    pass


class EncodingError(URLShortenerError):
    """Raised when encoding/decoding operations fail."""

    pass


class HTTPError(URLShortenerError):
    """Raised when HTTP processing fails."""

    pass
