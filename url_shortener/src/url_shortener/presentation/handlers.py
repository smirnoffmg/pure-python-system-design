"""
HTTP method handlers using decorators for clean separation of concerns.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from ..application import Shortener
from ..domain import ValidationError
from ..infrastructure import (
    HTTPRequest,
    HTTPResponse,
    get_logger,
    is_valid_url,
    normalize_url,
)

logger = get_logger(__name__)


class HandlerFunction(Protocol):
    """Protocol for handler functions with metadata."""

    _method: str
    _path: str

    def __call__(
        self, request: HTTPRequest, shortener: Shortener
    ) -> Awaitable[HTTPResponse]: ...


def json_response(
    status_code: int, status_message: str, data: dict[str, Any]
) -> HTTPResponse:
    """Create a JSON response."""
    return HTTPResponse(status_code, status_message, data)


def error_response(
    status_code: int, status_message: str, error_message: str
) -> HTTPResponse:
    """Create an error response with consistent error format."""
    return HTTPResponse(status_code, status_message, {"error": error_message})


def redirect_response(location: str) -> HTTPResponse:
    """Create a redirect response."""
    return HTTPResponse(302, "Found", headers={"Location": location})


def not_found() -> HTTPResponse:
    """Create a not found response."""
    return HTTPResponse(404, "Not Found")


def handle_errors(
    operation: str,
) -> Callable[
    [Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]]],
    Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]],
]:
    """Decorator for handling errors in HTTP handlers."""

    def decorator(
        func: Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]],
    ) -> Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]]:
        async def wrapper(request: HTTPRequest, shortener: Shortener) -> HTTPResponse:
            try:
                return await func(request, shortener)
            except ValidationError as e:
                logger.warning(f"Validation error in {operation}: {e}")
                return error_response(400, "Bad Request", str(e))
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error in {operation}: {e}")
                return error_response(400, "Bad Request", "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error in {operation}: {e}")
                return error_response(
                    500, "Internal Server Error", "Internal server error"
                )

        return wrapper

    return decorator


def post_handler(
    path: str,
) -> Callable[
    [Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]]], HandlerFunction
]:
    """Decorator for POST method handlers."""

    def decorator(
        func: Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]],
    ) -> HandlerFunction:
        wrapped = handle_errors(f"POST {path}")(func)
        wrapped._method = "POST"  # type: ignore
        wrapped._path = path  # type: ignore
        return wrapped  # type: ignore

    return decorator


def get_handler(
    path: str,
) -> Callable[
    [Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]]], HandlerFunction
]:
    """Decorator for GET method handlers."""

    def decorator(
        func: Callable[[HTTPRequest, Shortener], Awaitable[HTTPResponse]],
    ) -> HandlerFunction:
        wrapped = handle_errors(f"GET {path}")(func)
        wrapped._method = "GET"  # type: ignore
        wrapped._path = path  # type: ignore
        return wrapped  # type: ignore

    return decorator


@post_handler("/shorten")
async def handle_shorten(request: HTTPRequest, shortener: Shortener) -> HTTPResponse:
    """Handle POST /shorten requests."""
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
    short_code = await shortener.create_short_code(normalized_url)
    return json_response(201, "Created", {"short_code": short_code})


@get_handler("/<short_code>")
async def handle_redirect(request: HTTPRequest, shortener: Shortener) -> HTTPResponse:
    """Handle GET /<short_code> requests."""
    short_code = request.path.lstrip("/")
    full_url = await shortener.get_full_url(short_code)

    if full_url:
        return redirect_response(full_url)
    else:
        return not_found()


class HandlerRegistry:
    """Registry for HTTP method handlers."""

    def __init__(self, shortener: Shortener):
        self.shortener = shortener
        self._handlers: dict[tuple[str, str], HandlerFunction] = {
            ("POST", "/shorten"): handle_shorten,
        }

    def get_handler(
        self, method: str, path: str
    ) -> Callable[[HTTPRequest], Awaitable[HTTPResponse]] | None:
        """Get handler for specific method and path."""
        # Exact match
        handler = self._handlers.get((method, path))
        if handler:

            async def wrapper(request: HTTPRequest) -> HTTPResponse:
                return await handler(request, self.shortener)

            return wrapper

        # Pattern match for redirects
        if method == "GET" and path.startswith("/"):

            async def wrapper(request: HTTPRequest) -> HTTPResponse:
                return await handle_redirect(request, self.shortener)

            return wrapper

        return None
