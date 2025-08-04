"""
HTTP-related exceptions for the infrastructure layer.
"""

from ..domain import URLShortenerError


class HTTPError(URLShortenerError):
    """Raised when HTTP processing fails."""

    pass
