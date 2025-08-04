"""
HTTP method handlers using strategy pattern.
"""

import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from .exceptions import ValidationError
from .logger import logger
from .service import Shortener
from .types import HTTPRequest, HTTPResponse
from .utils import is_valid_url, normalize_url


class ResponseBuilder:
    """
    Factory for creating common HTTP responses.
    """

    @staticmethod
    def json_response(
        status_code: int, status_message: str, data: dict[str, Any]
    ) -> HTTPResponse:
        return HTTPResponse(status_code, status_message, data)

    @staticmethod
    def error_response(
        status_code: int, status_message: str, error_message: str
    ) -> HTTPResponse:
        return HTTPResponse(status_code, status_message, {"error": error_message})

    @staticmethod
    def redirect_response(location: str) -> HTTPResponse:
        return HTTPResponse(302, "Found", headers={"Location": location})

    @staticmethod
    def not_found() -> HTTPResponse:
        return HTTPResponse(404, "Not Found")


class MethodHandler(ABC):
    """Base class for HTTP method handlers."""

    def __init__(self, shortener: Shortener):
        self.shortener = shortener

    @abstractmethod
    async def handle(self, request: HTTPRequest) -> HTTPResponse: ...

    async def _handle_errors(
        self, operation: str, handler_func: Callable[[], Awaitable[HTTPResponse]]
    ) -> HTTPResponse:
        """Common error handling pattern for handlers."""
        try:
            return await handler_func()
        except ValidationError as e:
            logger.warning(f"Validation error in {operation}: {e}")
            return ResponseBuilder.error_response(400, "Bad Request", str(e))
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error in {operation}: {e}")
            return ResponseBuilder.error_response(
                400, "Bad Request", "Invalid JSON format"
            )
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return ResponseBuilder.error_response(
                500, "Internal Server Error", "Internal server error"
            )


class ShortenHandler(MethodHandler):
    """Handles POST /shorten requests."""

    async def handle(self, request: HTTPRequest) -> HTTPResponse:
        async def _handle() -> HTTPResponse:
            if not request.body:
                raise ValidationError("Empty request body")

            data = json.loads(request.body)
            full_url = data.get("url")
            if not full_url:
                raise ValidationError("URL parameter is required")

            # Validate and normalize URL
            if not is_valid_url(full_url):
                raise ValidationError("Invalid URL format")

            normalized_url = normalize_url(full_url)
            short_url = await self.shortener.get_short_url(normalized_url)
            return ResponseBuilder.json_response(
                201, "Created", {"short_url": short_url}
            )

        return await self._handle_errors("POST /shorten", _handle)


class RedirectHandler(MethodHandler):
    """Handles GET /<short_code> requests."""

    async def handle(self, request: HTTPRequest) -> HTTPResponse:
        short_code = request.path.lstrip("/")

        async def _handle() -> HTTPResponse:
            full_url = await self.shortener.get_full_url(short_code)
            if full_url:
                return ResponseBuilder.redirect_response(full_url)
            else:
                return ResponseBuilder.not_found()

        return await self._handle_errors(f"GET /{short_code}", _handle)


class HandlerRegistry:
    """Registry for HTTP method handlers."""

    def __init__(self, shortener: Shortener):
        self.shortener = shortener
        self._handlers = {
            ("POST", "/shorten"): ShortenHandler(shortener),
        }

    def get_handler(self, method: str, path: str) -> MethodHandler | None:
        """Get handler for specific method and path."""
        # Exact match
        handler = self._handlers.get((method, path))
        if handler:
            return handler

        # Pattern match for redirects
        if method == "GET" and path.startswith("/"):
            return RedirectHandler(self.shortener)

        return None
