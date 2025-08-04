from abc import ABC, abstractmethod

from ..infrastructure import BaseStorage


class BaseShortener(ABC):
    storage: BaseStorage

    @abstractmethod
    async def create_short_code(self, url: str) -> str: ...

    @abstractmethod
    async def get_full_url(self, url: str) -> str | None: ...


class Shortener(BaseShortener):
    def __init__(self, storage: BaseStorage) -> None:
        """
        Initialize the Shortener with a specific storage backend.

        Args:
            storage (BaseStorage): The storage backend to use for storing and retrieving
            URLs.
        """
        self.storage = storage

    async def create_short_code(self, url: str) -> str:
        """
        Generate a short code from the given full URL.

        This method interacts with the storage backend to either retrieve an existing
        short code for the provided full URL or generate a new one if it does not exist.

        Args:
            url (str): The full URL to be shortened.

        Returns:
            str: The generated short code.
        """
        # logging, caching, stats, etc...
        return await self.storage.create_short_code(url)

    async def get_full_url(self, url: str) -> str | None:
        """
        Retrieve the full URL for the given short URL.

        This method interacts with the storage backend to find the corresponding
        full URL for the provided short URL. If no match is found, it returns `None`.

        Args:
            url (str): The short URL to be expanded.

        Returns:
            str | None: The full URL if found, otherwise `None`.
        """
        # logging, caching, stats, etc...
        return await self.storage.get_full_url(url)
