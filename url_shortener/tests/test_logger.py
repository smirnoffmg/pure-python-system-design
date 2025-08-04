"""
Tests for the logger module.
"""

import logging
import logging.handlers
from unittest.mock import patch

from url_shortener.infrastructure import get_logger

logger = get_logger(__name__)


class TestLogger:
    """Test logger functionality."""

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a logger instance."""
        test_logger = get_logger("test_logger")

        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test_logger"

    def test_get_logger_sets_level(self) -> None:
        """Test that get_logger sets the correct log level."""
        test_logger = get_logger("test_level_logger")

        assert test_logger.level == logging.INFO

    def test_get_logger_has_handlers(self) -> None:
        """Test that get_logger creates handlers."""
        test_logger = get_logger("test_handlers_logger")

        assert len(test_logger.handlers) > 0

    def test_get_logger_console_handler(self) -> None:
        """Test that get_logger creates a console handler."""
        test_logger = get_logger("test_console_logger")

        console_handlers = [
            h for h in test_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) > 0

    def test_get_logger_file_handler(self) -> None:
        """Test that get_logger creates a file handler."""
        test_logger = get_logger("test_file_logger")

        file_handlers = [
            h
            for h in test_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(file_handlers) > 0

    def test_get_logger_formatter(self) -> None:
        """Test that get_logger sets formatters on handlers."""
        test_logger = get_logger("test_formatter_logger")

        for handler in test_logger.handlers:
            assert handler.formatter is not None

    def test_get_logger_idempotent(self) -> None:
        """Test that get_logger is idempotent (returns same logger)."""
        logger1 = get_logger("test_idempotent")
        logger2 = get_logger("test_idempotent")

        assert logger1 is logger2

    def test_get_logger_different_names(self) -> None:
        """Test that get_logger returns different loggers for different names."""
        logger1 = get_logger("test_different1")
        logger2 = get_logger("test_different2")

        assert logger1 is not logger2

    def test_logger_module_logger(self) -> None:
        """Test that the module logger is properly configured."""
        assert isinstance(logger, logging.Logger)
        assert logger.name == "tests.test_logger"

    def test_logger_can_log_messages(self) -> None:
        """Test that the logger can actually log messages."""
        with patch("logging.StreamHandler.emit") as mock_emit:
            logger.info("Test message")
            mock_emit.assert_called()

    def test_file_handler_configuration(self) -> None:
        """Test that file handler is configured correctly."""
        test_logger = get_logger("test_file_config")

        file_handlers = [
            h
            for h in test_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(file_handlers) > 0

        file_handler = file_handlers[0]
        assert file_handler.maxBytes == 5 * 1024 * 1024  # 5 MB
        assert file_handler.backupCount == 3

    def test_console_handler_level(self) -> None:
        """Test that console handler has correct level."""
        test_logger = get_logger("test_console_level")

        console_handlers = [
            h for h in test_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(console_handlers) > 0

        console_handler = console_handlers[0]
        assert console_handler.level == logging.INFO

    def test_file_handler_level(self) -> None:
        """Test that file handler has correct level."""
        test_logger = get_logger("test_file_level")

        file_handlers = [
            h
            for h in test_logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(file_handlers) > 0

        file_handler = file_handlers[0]
        assert file_handler.level == logging.DEBUG
