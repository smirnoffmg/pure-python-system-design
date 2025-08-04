"""
Tests for the handlers module.
"""

import pytest

from url_shortener.application import Shortener
from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure import HTTPRequest, InMemoryStorage
from url_shortener.presentation import (
    HandlerRegistry,
    handle_redirect,
    handle_shorten,
)


class TestShortenHandler:
    """Test handle_shorten function."""

    @pytest.fixture
    def shortener(self) -> Shortener:
        """Create a Shortener instance."""
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        return Shortener(storage)

    @pytest.mark.asyncio
    async def test_handle_valid_request(self, shortener: Shortener) -> None:
        """Test handling a valid shorten request."""
        request = HTTPRequest(
            "POST",
            "/shorten",
            "HTTP/1.1",
            {"content-type": "application/json"},
            '{"url": "http://example.com"}',
        )

        response = await handle_shorten(request, shortener)

        assert response.status_code == 201
        assert "short_code" in response.body

    @pytest.mark.asyncio
    async def test_handle_empty_body(self, shortener: Shortener) -> None:
        """Test handling a request with empty body."""
        request = HTTPRequest("POST", "/shorten", "HTTP/1.1", {}, None)

        response = await handle_shorten(request, shortener)

        assert response.status_code == 400
        assert response.body["error"] == "Empty request body"

    @pytest.mark.asyncio
    async def test_handle_missing_url(self, shortener: Shortener) -> None:
        """Test handling a request with missing URL."""
        request = HTTPRequest(
            "POST",
            "/shorten",
            "HTTP/1.1",
            {"content-type": "application/json"},
            '{"other_field": "value"}',
        )

        response = await handle_shorten(request, shortener)

        assert response.status_code == 400
        assert response.body["error"] == "URL parameter is required"

    @pytest.mark.asyncio
    async def test_handle_invalid_json(self, shortener: Shortener) -> None:
        """Test handling a request with invalid JSON."""
        request = HTTPRequest(
            "POST",
            "/shorten",
            "HTTP/1.1",
            {"content-type": "application/json"},
            '{"url": "http://example.com"',  # Missing closing brace
        )

        response = await handle_shorten(request, shortener)

        assert response.status_code == 400
        assert response.body["error"] == "Invalid JSON format"

    @pytest.mark.asyncio
    async def test_handle_invalid_url(self, shortener: Shortener) -> None:
        """Test handling a request with invalid URL."""
        request = HTTPRequest(
            "POST",
            "/shorten",
            "HTTP/1.1",
            {"content-type": "application/json"},
            '{"url": "not-a-valid-url"}',
        )

        response = await handle_shorten(request, shortener)

        assert response.status_code == 400
        assert response.body["error"] == "Invalid URL format"

    @pytest.mark.asyncio
    async def test_handle_url_without_protocol(self, shortener: Shortener) -> None:
        """Test handling a URL without protocol (should be normalized)."""
        request = HTTPRequest(
            "POST",
            "/shorten",
            "HTTP/1.1",
            {"content-type": "application/json"},
            '{"url": "example.com"}',
        )

        response = await handle_shorten(request, shortener)

        assert (
            response.status_code == 400
        )  # Should fail validation since we require protocol
        assert response.body["error"] == "Invalid URL format"


class TestRedirectHandler:
    """Test handle_redirect function."""

    @pytest.fixture
    def shortener(self) -> Shortener:
        """Create a Shortener instance."""
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        return Shortener(storage)

    @pytest.mark.asyncio
    async def test_handle_existing_short_code(self, shortener: Shortener) -> None:
        """Test handling a request for an existing short code."""
        # Create a short URL
        short_url = await shortener.create_short_code("http://example.com")
        short_code = short_url.split("/")[-1]

        # Test redirect
        request = HTTPRequest("GET", f"/{short_code}", "HTTP/1.1", {})
        response = await handle_redirect(request, shortener)

        assert response.status_code == 302
        assert response.headers["Location"] == "http://example.com"

    @pytest.mark.asyncio
    async def test_handle_nonexistent_short_code(self, shortener: Shortener) -> None:
        """Test handling a request for a nonexistent short code."""
        request = HTTPRequest("GET", "/nonexistent", "HTTP/1.1", {})

        response = await handle_redirect(request, shortener)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handle_invalid_short_code(self, shortener: Shortener) -> None:
        """Test handling a request with invalid short code format."""
        request = HTTPRequest("GET", "/invalid-code!", "HTTP/1.1", {})

        response = await handle_redirect(request, shortener)

        assert response.status_code == 404


class TestHandlerRegistry:
    """Test HandlerRegistry class."""

    @pytest.fixture
    def registry(self) -> HandlerRegistry:
        """Create a HandlerRegistry instance."""
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        shortener = Shortener(storage)
        return HandlerRegistry(shortener)

    def test_get_handler_exact_match(self, registry: HandlerRegistry) -> None:
        """Test getting a handler for an exact match."""
        handler = registry.get_handler("POST", "/shorten")

        assert handler is not None
        assert callable(handler)

    def test_get_handler_pattern_match(self, registry: HandlerRegistry) -> None:
        """Test getting a handler for a pattern match."""
        handler = registry.get_handler("GET", "/abc123")

        assert handler is not None
        assert callable(handler)

    def test_get_handler_no_match(self, registry: HandlerRegistry) -> None:
        """Test getting a handler when no match is found."""
        handler = registry.get_handler("PUT", "/shorten")

        assert handler is None

    def test_get_handler_different_path(self, registry: HandlerRegistry) -> None:
        """Test getting a handler for a different path."""
        handler = registry.get_handler("POST", "/different")

        assert handler is None

    def test_get_handler_non_get_redirect(self, registry: HandlerRegistry) -> None:
        """Test that non-GET requests don't match redirect pattern."""
        handler = registry.get_handler("POST", "/abc123")

        assert handler is None
