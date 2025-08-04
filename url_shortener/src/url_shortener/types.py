"""
Common types and data structures for the URL shortener service.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class HTTPRequest:
    """Represents an HTTP request with parsed data."""

    method: str
    path: str
    version: str
    headers: dict[str, str]
    body: str | None = None


@dataclass
class HTTPResponse:
    """Represents an HTTP response."""

    status_code: int
    status_message: str
    body: dict[str, Any] | None = None
    headers: dict[str, str] | None = None
