"""
Factory functions for creating service components.
"""

from ..application import Shortener
from ..domain import BaseEncoder
from . import InMemoryStorage, SQLiteStorage
from .config import Config


def create_storage(config: Config, encoder: BaseEncoder) -> InMemoryStorage | SQLiteStorage:
    """Create storage instance based on configuration."""
    if config.storage.type == "memory":
        return InMemoryStorage(encoder)
    elif config.storage.type == "sqlite":
        return SQLiteStorage(encoder, config.storage.db_path)
    else:
        raise ValueError(f"Unknown storage type: {config.storage.type}")


def create_shortener(config: Config, encoder: BaseEncoder) -> Shortener:
    """Create shortener service with appropriate storage."""

    storage = create_storage(config, encoder)
    return Shortener(storage)
