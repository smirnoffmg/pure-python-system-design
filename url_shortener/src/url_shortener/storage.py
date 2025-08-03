import asyncio
import sqlite3
from abc import ABC, abstractmethod

from .encoder import BaseEncoder


class BaseStorage(ABC):
    encoder: BaseEncoder

    @abstractmethod
    async def get_short_url(self, full_url: str) -> str: ...

    @abstractmethod
    async def get_full_url(self, short_url: str) -> str | None: ...


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
        self.db_path = db_path
        self.encoder = encoder
        self._init_done = False

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize_sync(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS url_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_url TEXT UNIQUE NOT NULL
                )
                """
            )
            conn.commit()
        self._init_done = True

    async def _initialize(self) -> None:
        if not self._init_done:
            await asyncio.to_thread(self._initialize_sync)

    async def get_short_url(self, url: str) -> str:
        await self._initialize()

        def sync_get_or_insert() -> str:
            with self._connect() as conn:
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

        return await asyncio.to_thread(sync_get_or_insert)

    async def get_full_url(self, short_code: str) -> str | None:
        await self._initialize()

        def sync_get() -> str | None:
            try:
                id = self.encoder.decode(short_code)
            except Exception:
                return None
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT full_url FROM url_mapping WHERE id = ?", (id,)
                )
                row = cursor.fetchone()
                return row[0] if row else None

        return await asyncio.to_thread(sync_get)
