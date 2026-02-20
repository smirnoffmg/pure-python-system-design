"""
Tests for configuration management.
"""

import os
from unittest.mock import patch

import pytest

from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure.config import Config, ServerConfig, StorageConfig
from url_shortener.infrastructure.factory import create_shortener, create_storage


class TestServerConfig:
    """Test ServerConfig class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ServerConfig()
        assert config.host == "localhost"
        assert config.port == 8000
        assert config.workers == 1

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ServerConfig(host="0.0.0.0", port=9000, workers=4)
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.workers == 4


class TestStorageConfig:
    """Test StorageConfig class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = StorageConfig()
        assert config.type == "memory"
        assert config.db_path == ":memory:"

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = StorageConfig(type="sqlite", db_path="/tmp/test.db")
        assert config.type == "sqlite"
        assert config.db_path == "/tmp/test.db"


class TestConfig:
    """Test main Config class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = Config()
        assert config.server.host == "localhost"
        assert config.server.port == 8000
        assert config.storage.type == "memory"

    def test_validation_valid(self) -> None:
        """Test configuration validation with valid values."""
        config = Config(
            server=ServerConfig(host="0.0.0.0", port=9000, workers=2),
            storage=StorageConfig(type="sqlite", db_path="/tmp/test.db"),
        )
        # Should not raise any exceptions
        config.validate()

    def test_validation_invalid_port(self) -> None:
        """Test configuration validation with invalid port."""
        config = Config(server=ServerConfig(port=0))
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            config.validate()

        config = Config(server=ServerConfig(port=70000))
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            config.validate()

    def test_validation_invalid_workers(self) -> None:
        """Test configuration validation with invalid workers."""
        config = Config(server=ServerConfig(workers=0))
        with pytest.raises(ValueError, match="Workers must be at least 1"):
            config.validate()

    def test_validation_invalid_storage_type(self) -> None:
        """Test configuration validation with invalid storage type."""
        config = Config(storage=StorageConfig(type="invalid"))  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Storage type must be 'memory' or 'sqlite'"):
            config.validate()

    def test_validation_sqlite_without_path(self) -> None:
        """Test configuration validation for SQLite without path."""
        config = Config(storage=StorageConfig(type="sqlite", db_path=""))
        with pytest.raises(ValueError, match="SQLite storage requires a database path"):
            config.validate()

    @patch.dict(
        os.environ,
        {
            "URL_SHORTENER_HOST": "0.0.0.0",
            "URL_SHORTENER_PORT": "9000",
            "URL_SHORTENER_WORKERS": "4",
            "URL_SHORTENER_STORAGE": "sqlite",
            "URL_SHORTENER_DB_PATH": "/tmp/prod.db",
        },
    )
    def test_from_env(self) -> None:
        """Test loading configuration from environment variables."""
        config = Config.from_env()
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 9000
        assert config.server.workers == 4
        assert config.storage.type == "sqlite"
        assert config.storage.db_path == "/tmp/prod.db"

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_defaults(self) -> None:
        """Test loading configuration with default values when env vars are not set."""
        config = Config.from_env()
        assert config.server.host == "localhost"
        assert config.server.port == 8000
        assert config.server.workers == 1
        assert config.storage.type == "memory"
        assert config.storage.db_path == ":memory:"


class TestFactory:
    """Test factory functions."""

    def test_create_storage_memory(self) -> None:
        """Test creating in-memory storage."""
        config = Config(storage=StorageConfig(type="memory"))
        encoder = Base62Encoder()

        storage = create_storage(config, encoder)
        assert storage.__class__.__name__ == "InMemoryStorage"
        assert storage.encoder == encoder

    def test_create_storage_sqlite(self) -> None:
        """Test creating SQLite storage."""
        config = Config(storage=StorageConfig(type="sqlite", db_path="/tmp/test.db"))
        encoder = Base62Encoder()

        storage = create_storage(config, encoder)
        assert storage.__class__.__name__ == "SQLiteStorage"
        assert storage.encoder == encoder

    def test_create_storage_invalid_type(self) -> None:
        """Test creating storage with invalid type."""
        config = Config(storage=StorageConfig(type="invalid"))  # type: ignore[arg-type]
        encoder = Base62Encoder()

        with pytest.raises(ValueError, match="Unknown storage type: invalid"):
            create_storage(config, encoder)

    def test_create_shortener(self) -> None:
        """Test creating shortener service."""
        config = Config()
        encoder = Base62Encoder()

        shortener = create_shortener(config, encoder)
        assert shortener.__class__.__name__ == "Shortener"
        assert shortener.storage.encoder == encoder
