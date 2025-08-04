"""
Tests for the API module.
"""

import asyncio

import pytest

from url_shortener.api import (
    HTTPProtocol,
    HTTPRequestParser,
    HTTPResponseSerializer,
    RequestHandler,
)
from url_shortener.encoder import Base62Encoder
from url_shortener.handlers import ResponseBuilder
from url_shortener.service import Shortener
from url_shortener.storage import InMemoryStorage
from url_shortener.types import HTTPRequest, HTTPResponse


class TestHTTPRequest:
    """Test HTTPRequest class."""

    def test_http_request_creation(self) -> None:
        """Test creating an HTTPRequest instance."""
        headers = {"content-type": "application/json"}
        request = HTTPRequest(
            "POST", "/shorten", "HTTP/1.1", headers, '{"url": "http://example.com"}'
        )

        assert request.method == "POST"
        assert request.path == "/shorten"
        assert request.version == "HTTP/1.1"
        assert request.headers == headers
        assert request.body == '{"url": "http://example.com"}'


class TestHTTPRequestParser:
    """Test HTTPRequestParser class."""

    def test_parse_valid_request(self) -> None:
        """Test parsing a valid HTTP request."""
        raw_request = (
            b"POST /shorten HTTP/1.1\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 29\r\n"
            b"\r\n"
            b'{"url": "http://example.com"}'
        )

        request = HTTPRequestParser.parse(raw_request)

        assert request is not None
        assert request.method == "POST"
        assert request.path == "/shorten"
        assert request.version == "HTTP/1.1"
        assert request.headers["content-type"] == "application/json"
        assert request.body == '{"url": "http://example.com"}'

    def test_parse_incomplete_request(self) -> None:
        """Test parsing an incomplete HTTP request."""
        raw_request = b"POST /shorten HTTP/1.1\r\n"

        request = HTTPRequestParser.parse(raw_request)

        # Should return None for incomplete request (no headers)
        assert request is None

    def test_parse_invalid_request(self) -> None:
        """Test parsing an invalid HTTP request."""
        raw_request = b"INVALID REQUEST\r\n"

        request = HTTPRequestParser.parse(raw_request)

        assert request is None

    def test_parse_request_without_body(self) -> None:
        """Test parsing a request without body."""
        raw_request = b"GET /abc123 HTTP/1.1\r\n" b"Host: localhost:8000\r\n" b"\r\n"

        request = HTTPRequestParser.parse(raw_request)

        assert request is not None
        assert request.method == "GET"
        assert request.path == "/abc123"
        assert request.body == ""  # Empty string, not None

    def test_parse_request_with_content_length_zero(self) -> None:
        """Test parsing a request with Content-Length: 0."""
        raw_request = b"GET /abc123 HTTP/1.1\r\n" b"Content-Length: 0\r\n" b"\r\n"

        request = HTTPRequestParser.parse(raw_request)

        assert request is not None
        assert request.method == "GET"
        assert request.path == "/abc123"
        assert request.body == ""


class TestHTTPResponse:
    """Test HTTPResponse class."""

    def test_response_with_body(self) -> None:
        """Test creating a response with JSON body."""
        response = HTTPResponse(
            201, "Created", {"short_url": "http://localhost:8000/abc123"}
        )

        serialized = HTTPResponseSerializer.serialize(response)
        assert b"HTTP/1.1 201 Created" in serialized
        assert b"Content-Type: application/json" in serialized
        assert b'"short_url": "http://localhost:8000/abc123"' in serialized

    def test_response_without_body(self) -> None:
        """Test creating a response without body."""
        response = HTTPResponse(404, "Not Found")

        serialized = HTTPResponseSerializer.serialize(response)
        assert b"HTTP/1.1 404 Not Found" in serialized
        assert b"Content-Type: application/json" not in serialized

    def test_response_with_custom_headers(self) -> None:
        """Test creating a response with custom headers."""
        headers = {"Location": "http://example.com"}
        response = HTTPResponse(302, "Found", headers=headers)

        serialized = HTTPResponseSerializer.serialize(response)
        assert b"HTTP/1.1 302 Found" in serialized
        assert b"Location: http://example.com" in serialized


class TestResponseBuilder:
    """Test ResponseBuilder class."""

    def test_json_response(self) -> None:
        """Test creating a JSON response."""
        response = ResponseBuilder.json_response(
            201, "Created", {"short_url": "abc123"}
        )

        assert response.status_code == 201
        assert response.status_message == "Created"
        assert response.body == {"short_url": "abc123"}

    def test_error_response(self) -> None:
        """Test creating an error response."""
        response = ResponseBuilder.error_response(400, "Bad Request", "Invalid URL")

        assert response.status_code == 400
        assert response.status_message == "Bad Request"
        assert response.body == {"error": "Invalid URL"}

    def test_redirect_response(self) -> None:
        """Test creating a redirect response."""
        response = ResponseBuilder.redirect_response("http://example.com")

        assert response.status_code == 302
        assert response.status_message == "Found"
        assert response.headers["Location"] == "http://example.com"

    def test_not_found_response(self) -> None:
        """Test creating a not found response."""
        response = ResponseBuilder.not_found()

        assert response.status_code == 404
        assert response.status_message == "Not Found"


class TestRequestHandler:
    """Test RequestHandler class."""

    @pytest.fixture
    def handler(self) -> RequestHandler:
        """Create a RequestHandler instance."""
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        shortener = Shortener(storage)
        return RequestHandler(shortener)

    @pytest.mark.asyncio
    async def test_handle_shorten_request(self, handler: RequestHandler) -> None:
        """Test handling a shorten request."""
        request = HTTPRequest(
            "POST",
            "/shorten",
            "HTTP/1.1",
            {"content-type": "application/json"},
            '{"url": "http://example.com"}',
        )

        response = await handler.handle(request)

        assert response.status_code == 201
        assert "short_url" in response.body

    @pytest.mark.asyncio
    async def test_handle_redirect_request(self, handler: RequestHandler) -> None:
        """Test handling a redirect request."""
        # First create a short URL
        shorten_request = HTTPRequest(
            "POST",
            "/shorten",
            "HTTP/1.1",
            {"content-type": "application/json"},
            '{"url": "http://example.com"}',
        )
        shorten_response = await handler.handle(shorten_request)
        short_url = shorten_response.body["short_url"]
        short_code = short_url.split("/")[-1]

        # Then test redirect
        redirect_request = HTTPRequest("GET", f"/{short_code}", "HTTP/1.1", {})
        redirect_response = await handler.handle(redirect_request)

        assert redirect_response.status_code == 302
        assert redirect_response.headers["Location"] == "http://example.com"

    @pytest.mark.asyncio
    async def test_handle_not_found(self, handler: RequestHandler) -> None:
        """Test handling a not found request."""
        request = HTTPRequest("GET", "/nonexistent", "HTTP/1.1", {})

        response = await handler.handle(request)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handle_invalid_method(self, handler: RequestHandler) -> None:
        """Test handling an invalid HTTP method."""
        request = HTTPRequest("PUT", "/shorten", "HTTP/1.1", {})

        response = await handler.handle(request)

        assert response.status_code == 404


class TestHTTPProtocol:
    """Test HTTPProtocol class."""

    @pytest.fixture
    def protocol(self) -> HTTPProtocol:
        """Create an HTTPProtocol instance."""
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        shortener = Shortener(storage)
        handler = RequestHandler(shortener)
        return HTTPProtocol(handler)

    def test_connection_made(self, protocol: HTTPProtocol) -> None:
        """Test connection_made method."""

        # Mock transport
        class MockTransport:
            def write(self, data: bytes) -> None:
                pass

            def close(self) -> None:
                pass

        transport = MockTransport()
        protocol.connection_made(transport)

        assert protocol.transport == transport

    @pytest.mark.asyncio
    async def test_data_received_complete_request(self, protocol: HTTPProtocol) -> None:
        """Test data_received with a complete request."""
        raw_request = (
            b"POST /shorten HTTP/1.1\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 25\r\n"
            b"\r\n"
            b'{"url": "http://example.com"}'
        )

        # Mock transport
        class MockTransport:
            def __init__(self) -> None:
                self.written_data: bytes | None = None
                self.closed = False

            def write(self, data: bytes) -> None:
                self.written_data = data

            def close(self) -> None:
                self.closed = True

        transport = MockTransport()
        protocol.connection_made(transport)

        # Process the request
        protocol.data_received(raw_request)

        # Wait for async processing
        await asyncio.sleep(0.01)

        # Check that response was written
        assert transport.written_data is not None
        assert b"HTTP/1.1" in transport.written_data

    @pytest.mark.asyncio
    async def test_data_received_incomplete_request(
        self, protocol: HTTPProtocol
    ) -> None:
        """Test data_received with an incomplete request."""
        raw_request = b"POST /shorten HTTP/1.1\r\n"

        # Mock transport
        class MockTransport:
            def __init__(self) -> None:
                self.written_data: bytes | None = None
                self.closed = False

            def write(self, data: bytes) -> None:
                self.written_data = data

            def close(self) -> None:
                self.closed = True

        transport = MockTransport()
        protocol.connection_made(transport)

        # Process the request
        protocol.data_received(raw_request)

        # Check that no response was written (incomplete request)
        assert transport.written_data is None
        assert not transport.closed
