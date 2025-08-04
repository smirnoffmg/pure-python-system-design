"""
Presentation layer - HTTP handlers and API endpoints.
"""

from ..infrastructure import HTTPError, HTTPRequest, HTTPResponse
from .api import HTTPProtocol, RequestHandler, serve
from .handlers import (
    HandlerRegistry,
    error_response,
    get_handler,
    handle_errors,
    handle_redirect,
    handle_shorten,
    json_response,
    not_found,
    post_handler,
    redirect_response,
)

__all__ = [
    "HTTPProtocol",
    "RequestHandler",
    "serve",
    "HTTPRequest",
    "HTTPResponse",
    "HTTPError",
    "HandlerRegistry",
    "handle_shorten",
    "handle_redirect",
    "json_response",
    "error_response",
    "redirect_response",
    "not_found",
    "post_handler",
    "get_handler",
    "handle_errors",
]
