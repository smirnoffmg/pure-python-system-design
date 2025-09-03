"""
Configuration management for the URL shortener service.
"""

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ServerConfig:
    """Server configuration settings."""

    host: str = "localhost"
    port: int = 8000
    workers: int = 1


@dataclass
class StorageConfig:
    """Storage configuration settings."""

    type: Literal["memory", "sqlite"] = "memory"
    db_path: str = ":memory:"


@dataclass
class Config:
    """Main configuration class."""

    server: ServerConfig = field(default_factory=ServerConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            server=ServerConfig(
                host=os.getenv("URL_SHORTENER_HOST", "localhost"),
                port=int(os.getenv("URL_SHORTENER_PORT", "8000")),
                workers=int(os.getenv("URL_SHORTENER_WORKERS", "1")),
            ),
            storage=StorageConfig(
                type=os.getenv("URL_SHORTENER_STORAGE", "memory"),  # type: ignore
                db_path=os.getenv("URL_SHORTENER_DB_PATH", ":memory:"),
            ),
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if self.server.port < 1 or self.server.port > 65535:
            raise ValueError("Port must be between 1 and 65535")

        if self.server.workers < 1:
            raise ValueError("Workers must be at least 1")

        if self.storage.type not in ("memory", "sqlite"):
            raise ValueError("Storage type must be 'memory' or 'sqlite'")

        if self.storage.type == "sqlite" and not self.storage.db_path:
            raise ValueError("SQLite storage requires a database path")
