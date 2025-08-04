"""
Infrastructure layer - External concerns (storage, HTTP, logging).
"""

from .database import DatabaseManager
from .exceptions import HTTPError
from .http_parser import HTTPRequestParser
from .http_serializer import HTTPResponseSerializer
from .logger import get_logger
from .storage import BaseStorage, InMemoryStorage, SQLiteStorage
from .types import HTTPRequest, HTTPResponse
from .utils import extract_domain, is_valid_url, normalize_url

__all__ = [
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
]
