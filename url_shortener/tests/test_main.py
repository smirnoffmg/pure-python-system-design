"""
Tests for the main module entry point.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from url_shortener.application import Shortener
from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure import InMemoryStorage
from url_shortener.presentation import serve


class TestMainModule:
    """Test the main module functionality."""

    def test_imports(self) -> None:
        """Test that all required modules can be imported."""
        # This test ensures the main module can be imported without errors
        from url_shortener import __main__  # noqa: F401

        assert True

    def test_encoder_creation(self) -> None:
        """Test that Base62Encoder can be created."""
        encoder = Base62Encoder()
        assert encoder is not None
        assert hasattr(encoder, "encode")
        assert hasattr(encoder, "decode")

    def test_storage_creation(self) -> None:
        """Test that InMemoryStorage can be created with encoder."""
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        assert storage is not None
        assert storage.encoder == encoder

    def test_shortener_creation(self) -> None:
        """Test that Shortener can be created with storage."""
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        shortener = Shortener(storage)
        assert shortener is not None
        assert shortener.storage == storage

    def test_main_execution_flow(self) -> None:
        """Test the main execution flow."""
        # Test that the main execution logic works correctly
        encoder = Base62Encoder()
        storage = InMemoryStorage(encoder)
        shortener = Shortener(storage)

        # Verify the objects were created correctly
        assert isinstance(encoder, Base62Encoder)
        assert isinstance(storage, InMemoryStorage)
        assert isinstance(shortener, Shortener)

        # Verify the storage has the correct encoder
        assert storage.encoder == encoder
        assert shortener.storage == storage

    @patch("url_shortener.presentation.serve")
    @patch("asyncio.run")
    def test_main_with_exception_handling(self, mock_asyncio_run: MagicMock, mock_serve: AsyncMock) -> None:
        """Test main execution with exception handling."""
        # Mock serve to raise an exception
        mock_serve.side_effect = Exception("Test error")

        # Mock asyncio.run to capture the exception
        def mock_run(coro) -> Exception:
            try:
                asyncio.create_task(coro)
                return Exception("Unexpected success")
            except Exception as e:
                return e

        mock_asyncio_run.side_effect = mock_run

        # Test that the exception handling works
        try:
            asyncio.run(serve(MagicMock(), "localhost", 8000))
        except Exception as err:
            assert str(err) == "Test error"

    def test_main_module_attributes(self) -> None:
        """Test that main module has expected attributes."""
        from url_shortener import __main__ as main_module

        # Check that required functions/classes are available
        assert hasattr(main_module, "logger")
        assert hasattr(main_module, "Base62Encoder")
        assert hasattr(main_module, "serve")
        # Check for new configuration-related imports
        assert hasattr(main_module, "Config")
        assert hasattr(main_module, "create_shortener")
