import asyncio
import sqlite3
from abc import ABC, abstractmethod

from .database import DatabaseManager
from .encoder import BaseEncoder
from .exceptions import StorageError


class ReadStorage(ABC):
    """Interface for read-only storage operations."""

    @abstractmethod
    async def get_full_url(self, short_url: str) -> str | None: ...


class WriteStorage(ABC):
    """Interface for write-only storage operations."""

    @abstractmethod
    async def get_short_url(self, full_url: str) -> str: ...


class BaseStorage(ReadStorage, WriteStorage):
    """Combined interface for read-write storage operations."""

    encoder: BaseEncoder


class InMemoryStorage(BaseStorage):
    def __init__(self, encoder: BaseEncoder) -> None:
        self.encoder = encoder

        self.full_x_short = dict[str, str]()
        self.short_x_full = dict[str, str]()

        self.lock = asyncio.Lock()
        self._length = 0

    async def get_short_url(self, full_url: str) -> str:
        """
        Get the short URL for a given full URL.

        Args:
            full_url (str): The full URL to be shortened.

        Returns:
            str: The short URL.
        """
        async with self.lock:
            if full_url in self.full_x_short:
                return self.full_x_short[full_url]

            new_length = self._length + 1
            short_url = self.encoder.encode(new_length)
            self.full_x_short[full_url] = short_url
            self.short_x_full[short_url] = full_url

            self._length = new_length  # Update length after successful encoding

            return short_url

    async def get_full_url(self, short_url: str) -> str | None:
        """
        Get the full URL for a given short URL.

        Args:
            short_url (str): The short URL to be expanded.

        Returns:
            str | None: The full URL if found, otherwise None.
        """
        async with self.lock:
            return self.short_x_full.get(short_url, None)


class SQLiteStorage(BaseStorage):
    def __init__(self, encoder: BaseEncoder, db_path: str = ":memory:"):
        self.db_manager = DatabaseManager(db_path)
        self.encoder = encoder
        self._init_done = False

    def _connect(self) -> sqlite3.Connection:
        """Get a database connection (for testing compatibility)."""
        return self.db_manager._connect()

    def _initialize_sync(self) -> None:
        """Initialize the database synchronously."""
        self.db_manager.initialize()
        self._init_done = True

    async def _initialize(self) -> None:
        """Initialize the database asynchronously."""
        if not self._init_done:
            await asyncio.to_thread(self._initialize_sync)

    async def get_short_url(self, url: str) -> str:
        await self._initialize()

        def sync_get_or_insert() -> str:
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT id FROM url_mapping WHERE full_url = ?", (url,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return self.encoder.encode(row[0])

                    cursor = conn.execute(
                        "INSERT INTO url_mapping (full_url) VALUES (?)", (url,)
                    )
                    conn.commit()
                    last_id = cursor.lastrowid or 1
                    return self.encoder.encode(last_id)
            except Exception as e:
                raise StorageError(f"Failed to get or insert URL: {e}") from e

        return await asyncio.to_thread(sync_get_or_insert)

    async def get_full_url(self, short_code: str) -> str | None:
        await self._initialize()

        def sync_get() -> str | None:
            try:
                id = self.encoder.decode(short_code)
                # Check if the decoded ID is reasonable (not too large for SQLite)
                if id > 9223372036854775807:  # SQLite INTEGER max value
                    return None
            except (Exception, OverflowError):
                # Return None for invalid codes instead of raising
                return None

            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT full_url FROM url_mapping WHERE id = ?", (id,)
                    )
                    row = cursor.fetchone()
                    return row[0] if row else None
            except Exception as e:
                raise StorageError(f"Failed to get full URL: {e}") from e

        return await asyncio.to_thread(sync_get)
