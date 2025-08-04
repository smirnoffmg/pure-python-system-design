"""
Benchmark tests for the URL shortener service.
"""

import asyncio
import tempfile
from typing import Any

import pytest

from url_shortener.application import Shortener
from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure import (
    HTTPRequestParser,
    HTTPResponse,
    HTTPResponseSerializer,
    InMemoryStorage,
    SQLiteStorage,
    extract_domain,
    is_valid_url,
    normalize_url,
)
from url_shortener.presentation import (
    error_response,
    json_response,
    not_found,
    redirect_response,
)


class TestEncoderBenchmarks:
    """Benchmark tests for Base62Encoder."""

    @pytest.fixture
    def encoder(self) -> Base62Encoder:
        """Create a Base62Encoder instance."""
        return Base62Encoder()

    def test_encode_small_numbers(self, encoder: Base62Encoder, benchmark: Any) -> None:
        """Benchmark encoding small numbers."""

        def encode_small():
            for i in range(1000):
                encoder.encode(i)

        benchmark(encode_small)

    def test_encode_large_numbers(self, encoder: Base62Encoder, benchmark: Any) -> None:
        """Benchmark encoding large numbers."""

        def encode_large():
            for i in range(1000000, 1001000):
                encoder.encode(i)

        benchmark(encode_large)

    def test_decode_small_strings(self, encoder: Base62Encoder, benchmark: Any) -> None:
        """Benchmark decoding small strings."""
        # Pre-generate some encoded strings
        encoded_strings = [encoder.encode(i) for i in range(1000)]

        def decode_small():
            for s in encoded_strings:
                encoder.decode(s)

        benchmark(decode_small)

    def test_decode_large_strings(self, encoder: Base62Encoder, benchmark: Any) -> None:
        """Benchmark decoding large strings."""
        # Pre-generate some large encoded strings
        encoded_strings = [encoder.encode(i) for i in range(1000000, 1001000)]

        def decode_large():
            for s in encoded_strings:
                encoder.decode(s)

        benchmark(decode_large)

    def test_encode_decode_roundtrip(
        self, encoder: Base62Encoder, benchmark: Any
    ) -> None:
        """Benchmark encode-decode roundtrip."""

        def roundtrip():
            for i in range(1000):
                encoded = encoder.encode(i)
                decoded = encoder.decode(encoded)
                assert decoded == i

        benchmark(roundtrip)


class TestStorageBenchmarks:
    """Benchmark tests for storage implementations."""

    @pytest.fixture
    def encoder(self) -> Base62Encoder:
        """Create a Base62Encoder instance."""
        return Base62Encoder()

    @pytest.fixture
    def in_memory_storage(self, encoder: Base62Encoder) -> InMemoryStorage:
        """Create an InMemoryStorage instance."""
        return InMemoryStorage(encoder)

    @pytest.fixture
    def sqlite_storage(self, encoder: Base62Encoder) -> SQLiteStorage:
        """Create a SQLiteStorage instance with file-based database."""
        # Use a temporary file instead of in-memory database
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()

        storage = SQLiteStorage(encoder, temp_file.name)
        # Initialize the database
        asyncio.run(storage._initialize())

        # Clean up the file after the test
        import atexit

        atexit.register(lambda: temp_file.close() if not temp_file.closed else None)

        return storage

    def test_in_memory_get_short_url(
        self, in_memory_storage: InMemoryStorage, benchmark: Any
    ) -> None:
        """Benchmark getting short URLs from in-memory storage."""
        urls = [f"http://example{i}.com" for i in range(1000)]

        def get_short_urls():
            async def _async_operation():
                for url in urls:
                    await in_memory_storage.create_short_code(url)

            asyncio.run(_async_operation())

        benchmark(get_short_urls)

    def test_in_memory_get_full_url(
        self, in_memory_storage: InMemoryStorage, benchmark: Any
    ) -> None:
        """Benchmark getting full URLs from in-memory storage."""
        # Pre-populate storage
        urls = [f"http://example{i}.com" for i in range(1000)]

        async def _setup():
            short_urls = []
            for url in urls:
                short_url = await in_memory_storage.create_short_code(url)
                short_urls.append(short_url)
            return short_urls

        short_urls = asyncio.run(_setup())

        def get_full_urls():
            async def _async_operation():
                for short_url in short_urls:
                    await in_memory_storage.get_full_url(short_url)

            asyncio.run(_async_operation())

        benchmark(get_full_urls)

    def test_sqlite_get_short_url(
        self, sqlite_storage: SQLiteStorage, benchmark: Any
    ) -> None:
        """Benchmark getting short URLs from SQLite storage."""
        urls = [f"http://example{i}.com" for i in range(100)]

        def get_short_urls():
            async def _async_operation():
                for url in urls:
                    await sqlite_storage.create_short_code(url)

            asyncio.run(_async_operation())

        benchmark(get_short_urls)

    def test_sqlite_get_full_url(
        self, sqlite_storage: SQLiteStorage, benchmark: Any
    ) -> None:
        """Benchmark getting full URLs from SQLite storage."""
        # Pre-populate storage
        urls = [f"http://example{i}.com" for i in range(100)]

        async def _setup():
            short_urls = []
            for url in urls:
                short_url = await sqlite_storage.create_short_code(url)
                short_urls.append(short_url)
            return short_urls

        short_urls = asyncio.run(_setup())

        def get_full_urls():
            async def _async_operation():
                for short_url in short_urls:
                    await sqlite_storage.get_full_url(short_url)

            asyncio.run(_async_operation())

        benchmark(get_full_urls)

    def test_concurrent_in_memory_operations(
        self, in_memory_storage: InMemoryStorage, benchmark: Any
    ) -> None:
        """Benchmark concurrent operations on in-memory storage."""
        urls = [f"http://example{i}.com" for i in range(100)]

        def concurrent_operations():
            async def _async_operation():
                tasks = [in_memory_storage.create_short_code(url) for url in urls]
                await asyncio.gather(*tasks)

            asyncio.run(_async_operation())

        benchmark(concurrent_operations)

    def test_concurrent_sqlite_operations(
        self, sqlite_storage: SQLiteStorage, benchmark: Any
    ) -> None:
        """Benchmark concurrent operations on SQLite storage."""
        urls = [f"http://example{i}.com" for i in range(50)]

        def concurrent_operations():
            async def _async_operation():
                tasks = [sqlite_storage.create_short_code(url) for url in urls]
                await asyncio.gather(*tasks)

            asyncio.run(_async_operation())

        benchmark(concurrent_operations)


class TestServiceBenchmarks:
    """Benchmark tests for the Shortener service."""

    @pytest.fixture
    def encoder(self) -> Base62Encoder:
        """Create a Base62Encoder instance."""
        return Base62Encoder()

    @pytest.fixture
    def in_memory_shortener(self, encoder: Base62Encoder) -> Shortener:
        """Create a Shortener with InMemoryStorage."""
        storage = InMemoryStorage(encoder)
        return Shortener(storage)

    @pytest.fixture
    def sqlite_shortener(self, encoder: Base62Encoder) -> Shortener:
        """Create a Shortener with SQLiteStorage."""
        # Use a temporary file instead of in-memory database
        temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_file.close()

        storage = SQLiteStorage(encoder, temp_file.name)
        # Initialize the database
        asyncio.run(storage._initialize())

        # Clean up the file after the test
        import atexit

        atexit.register(lambda: temp_file.close() if not temp_file.closed else None)

        return Shortener(storage)

    def test_in_memory_shorten_urls(
        self, in_memory_shortener: Shortener, benchmark: Any
    ) -> None:
        """Benchmark shortening URLs with in-memory storage."""
        urls = [f"http://example{i}.com" for i in range(1000)]

        def shorten_urls():
            async def _async_operation():
                for url in urls:
                    await in_memory_shortener.create_short_code(url)

            asyncio.run(_async_operation())

        benchmark(shorten_urls)

    def test_sqlite_shorten_urls(
        self, sqlite_shortener: Shortener, benchmark: Any
    ) -> None:
        """Benchmark shortening URLs with SQLite storage."""
        urls = [f"http://example{i}.com" for i in range(100)]

        def shorten_urls():
            async def _async_operation():
                for url in urls:
                    await sqlite_shortener.create_short_code(url)

            asyncio.run(_async_operation())

        benchmark(shorten_urls)

    def test_in_memory_expand_urls(
        self, in_memory_shortener: Shortener, benchmark: Any
    ) -> None:
        """Benchmark expanding URLs with in-memory storage."""
        # Pre-populate with short URLs
        urls = [f"http://example{i}.com" for i in range(1000)]

        async def _setup():
            short_urls = []
            for url in urls:
                short_url = await in_memory_shortener.create_short_code(url)
                short_urls.append(short_url)
            return short_urls

        short_urls = asyncio.run(_setup())

        def expand_urls():
            async def _async_operation():
                for short_url in short_urls:
                    await in_memory_shortener.get_full_url(short_url)

            asyncio.run(_async_operation())

        benchmark(expand_urls)

    def test_sqlite_expand_urls(
        self, sqlite_shortener: Shortener, benchmark: Any
    ) -> None:
        """Benchmark expanding URLs with SQLite storage."""
        # Pre-populate with short URLs
        urls = [f"http://example{i}.com" for i in range(100)]

        async def _setup():
            short_urls = []
            for url in urls:
                short_url = await sqlite_shortener.create_short_code(url)
                short_urls.append(short_url)
            return short_urls

        short_urls = asyncio.run(_setup())

        def expand_urls():
            async def _async_operation():
                for short_url in short_urls:
                    await sqlite_shortener.get_full_url(short_url)

            asyncio.run(_async_operation())

        benchmark(expand_urls)


class TestUtilsBenchmarks:
    """Benchmark tests for utility functions."""

    def test_is_valid_url_benchmark(self, benchmark: Any) -> None:
        """Benchmark URL validation."""
        urls = [
            "http://example.com",
            "https://example.com/path",
            "http://localhost:8080",
            "ftp://example.com",  # Invalid
            "not-a-url",  # Invalid
            "http://example.com/path?param=value",
            "https://subdomain.example.com:8080/path",
        ] * 100  # Repeat to get more data points

        def validate_urls():
            for url in urls:
                is_valid_url(url)

        benchmark(validate_urls)

    def test_normalize_url_benchmark(self, benchmark: Any) -> None:
        """Benchmark URL normalization."""
        urls = [
            "example.com",
            "http://example.com",
            "https://example.com",
            "subdomain.example.com",
            "example.com/path",
        ] * 100

        def normalize_urls():
            for url in urls:
                normalize_url(url)

        benchmark(normalize_urls)

    def test_extract_domain_benchmark(self, benchmark: Any) -> None:
        """Benchmark domain extraction."""
        urls = [
            "http://example.com",
            "https://subdomain.example.com",
            "http://example.com/path",
            "https://example.com:8080",
            "http://localhost:3000",
        ] * 100

        def extract_domains():
            for url in urls:
                extract_domain(url)

        benchmark(extract_domains)


class TestAPIBenchmarks:
    """Benchmark tests for API components."""

    def test_http_request_parsing(self, benchmark: Any) -> None:
        """Benchmark HTTP request parsing."""
        raw_requests = [
            b"POST /shorten HTTP/1.1\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 25\r\n"
            b"\r\n"
            b'{"url": "http://example.com"}',
            b"GET /abc123 HTTP/1.1\r\n" b"Host: localhost:8000\r\n" b"\r\n",
            b"POST /shorten HTTP/1.1\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 30\r\n"
            b"\r\n"
            b'{"url": "http://test.com"}',
        ] * 50

        def parse_requests():
            for raw_request in raw_requests:
                HTTPRequestParser.parse(raw_request)

        benchmark(parse_requests)

    def test_http_response_serialization(self, benchmark: Any) -> None:
        """Benchmark HTTP response serialization."""
        responses = [
            HTTPResponse(201, "Created", {"short_code": "abc123"}),
            HTTPResponse(404, "Not Found"),
            HTTPResponse(302, "Found", headers={"Location": "http://example.com"}),
            HTTPResponse(400, "Bad Request", {"error": "Invalid URL"}),
        ] * 50

        def serialize_responses():
            for response in responses:
                HTTPResponseSerializer.serialize(response)

        benchmark(serialize_responses)

    def test_response_builder_benchmark(self, benchmark: Any) -> None:
        """Benchmark response builder operations."""

        def build_responses():
            for i in range(1000):
                json_response(201, "Created", {"short_code": f"abc{i}"})
            error_response(400, "Bad Request", "Invalid URL")
            redirect_response(f"http://example{i}.com")
            not_found()

        benchmark(build_responses)


class TestEndToEndBenchmarks:
    """Benchmark tests for end-to-end operations."""

    @pytest.fixture
    def encoder(self) -> Base62Encoder:
        """Create a Base62Encoder instance."""
        return Base62Encoder()

    @pytest.fixture
    def in_memory_shortener(self, encoder: Base62Encoder) -> Shortener:
        """Create a Shortener with InMemoryStorage."""
        storage = InMemoryStorage(encoder)
        return Shortener(storage)

    def test_end_to_end_shorten_expand(
        self, in_memory_shortener: Shortener, benchmark: Any
    ) -> None:
        """Benchmark complete shorten and expand operations."""
        urls = [f"http://example{i}.com" for i in range(100)]

        def end_to_end_operations():
            async def _async_operation():
                for url in urls:
                    # Shorten
                    short_url = await in_memory_shortener.create_short_code(url)
                    # Expand
                    expanded_url = await in_memory_shortener.get_full_url(short_url)
                    assert expanded_url == url

            asyncio.run(_async_operation())

        benchmark(end_to_end_operations)

    def test_concurrent_end_to_end(
        self, in_memory_shortener: Shortener, benchmark: Any
    ) -> None:
        """Benchmark concurrent end-to-end operations."""
        urls = [f"http://example{i}.com" for i in range(50)]

        async def single_operation(url: str) -> None:
            short_url = await in_memory_shortener.create_short_code(url)
            expanded_url = await in_memory_shortener.get_full_url(short_url)
            assert expanded_url == url

        def concurrent_operations():
            async def _async_operation():
                tasks = [single_operation(url) for url in urls]
                await asyncio.gather(*tasks)

            asyncio.run(_async_operation())

        benchmark(concurrent_operations)
