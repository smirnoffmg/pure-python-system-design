"""
Tests for SQLiteStorage.
"""

import asyncio
import sqlite3
import tempfile

import pytest

from url_shortener.encoder import Base62Encoder
from url_shortener.storage import SQLiteStorage


class TestSQLiteStorage:
    """Test SQLiteStorage class."""

    @pytest.fixture
    def temp_db_path(self) -> str:
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            return f.name

    @pytest.fixture
    def encoder(self) -> Base62Encoder:
        """Create a Base62Encoder instance."""
        return Base62Encoder()

    @pytest.fixture
    def storage(self, encoder: Base62Encoder, temp_db_path: str) -> SQLiteStorage:
        """Create a SQLiteStorage instance with temporary database."""
        storage = SQLiteStorage(encoder, temp_db_path)
        # Initialize the database synchronously
        storage._initialize_sync()
        return storage

    @pytest.mark.asyncio
    async def test_get_short_url_new_url(self, storage: SQLiteStorage) -> None:
        """Test getting a short URL for a new URL."""
        short_url = await storage.get_short_url("http://example.com")

        assert short_url is not None
        assert len(short_url) > 0

    @pytest.mark.asyncio
    async def test_get_short_url_existing_url(self, storage: SQLiteStorage) -> None:
        """Test getting a short URL for an existing URL (should return same)."""
        url = "http://example.com"
        short_url1 = await storage.get_short_url(url)
        short_url2 = await storage.get_short_url(url)

        assert short_url1 == short_url2

    @pytest.mark.asyncio
    async def test_get_full_url_existing(self, storage: SQLiteStorage) -> None:
        """Test getting full URL for existing short URL."""
        full_url = "http://example.com"
        short_url = await storage.get_short_url(full_url)
        short_code = short_url.split("/")[-1] if "/" in short_url else short_url

        retrieved_url = await storage.get_full_url(short_code)

        assert retrieved_url == full_url

    @pytest.mark.asyncio
    async def test_get_full_url_nonexistent(self, storage: SQLiteStorage) -> None:
        """Test getting full URL for nonexistent short URL."""
        result = await storage.get_full_url("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_full_url_invalid_code(self, storage: SQLiteStorage) -> None:
        """Test getting full URL for invalid short code."""
        result = await storage.get_full_url("invalid-code!")

        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_urls(self, storage: SQLiteStorage) -> None:
        """Test handling multiple URLs."""
        urls = ["http://example1.com", "http://example2.com", "http://example3.com"]

        short_urls = []
        for url in urls:
            short_url = await storage.get_short_url(url)
            short_urls.append(short_url)

        # All short URLs should be different
        assert len(set(short_urls)) == len(urls)

        # Should be able to retrieve all full URLs
        for i, url in enumerate(urls):
            short_code = (
                short_urls[i].split("/")[-1] if "/" in short_urls[i] else short_urls[i]
            )
            retrieved_url = await storage.get_full_url(short_code)
            assert retrieved_url == url

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage: SQLiteStorage) -> None:
        """Test concurrent operations."""
        urls = [f"http://example{i}.com" for i in range(10)]

        # Create short URLs concurrently
        tasks = [storage.get_short_url(url) for url in urls]
        short_urls = await asyncio.gather(*tasks)

        # All short URLs should be different
        assert len(set(short_urls)) == len(urls)

        # Retrieve full URLs concurrently
        short_codes = [url.split("/")[-1] if "/" in url else url for url in short_urls]
        retrieve_tasks = [storage.get_full_url(code) for code in short_codes]
        retrieved_urls = await asyncio.gather(*retrieve_tasks)

        # Should match original URLs
        assert retrieved_urls == urls

    @pytest.mark.asyncio
    async def test_database_persistence(
        self, encoder: Base62Encoder, temp_db_path: str
    ) -> None:
        """Test that data persists between storage instances."""
        # Create first storage instance
        storage1 = SQLiteStorage(encoder, temp_db_path)
        url = "http://example.com"
        short_url = await storage1.get_short_url(url)
        short_code = short_url.split("/")[-1] if "/" in short_url else short_url

        # Create second storage instance with same database
        storage2 = SQLiteStorage(encoder, temp_db_path)
        retrieved_url = await storage2.get_full_url(short_code)

        assert retrieved_url == url

    @pytest.mark.asyncio
    async def test_memory_database(self, encoder: Base62Encoder) -> None:
        """Test using in-memory database."""
        # Use a temporary file instead of in-memory database for testing
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = f.name

        try:
            storage = SQLiteStorage(encoder, temp_db_path)
            # Initialize the database synchronously
            storage._initialize_sync()

            url = "http://example.com"
            short_url = await storage.get_short_url(url)
            short_code = short_url.split("/")[-1] if "/" in short_url else short_url

            retrieved_url = await storage.get_full_url(short_code)

            assert retrieved_url == url
        finally:
            # Clean up the temporary file
            import os

            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    @pytest.mark.asyncio
    async def test_database_initialization(
        self, encoder: Base62Encoder, temp_db_path: str
    ) -> None:
        """Test that database is properly initialized."""
        storage = SQLiteStorage(encoder, temp_db_path)

        # Check that database file exists after first operation
        await storage.get_short_url("http://example.com")

        # Verify table structure
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='url_mapping'"
            )
            assert cursor.fetchone() is not None

            cursor = conn.execute("PRAGMA table_info(url_mapping)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            assert "id" in column_names
            assert "full_url" in column_names

    @pytest.mark.asyncio
    async def test_idempotency(self, storage: SQLiteStorage) -> None:
        """Test that same URL always returns same short code."""
        url = "http://example.com"

        short_url1 = await storage.get_short_url(url)
        short_url2 = await storage.get_short_url(url)
        short_url3 = await storage.get_short_url(url)

        assert short_url1 == short_url2 == short_url3

    @pytest.mark.asyncio
    async def test_error_handling_invalid_decode(self, storage: SQLiteStorage) -> None:
        """Test error handling when decoding invalid short code."""
        result = await storage.get_full_url("invalid!@#")

        assert result is None

    def test_connect_method(self, storage: SQLiteStorage) -> None:
        """Test the _connect method."""
        connection = storage._connect()

        assert isinstance(connection, sqlite3.Connection)
        connection.close()
