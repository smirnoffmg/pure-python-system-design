import pytest

from url_shortener.utils import extract_domain, is_valid_url, normalize_url


class TestURLValidation:
    """Test URL validation utilities."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("http://example.com", True),
            ("https://example.com", True),
            ("http://example.com/path", True),
            ("https://example.com/path?param=value", True),
            ("http://localhost:8080", True),
            ("http://127.0.0.1", True),
            ("http://192.168.1.1:3000", True),
            ("example.com", False),  # Missing protocol
            ("ftp://example.com", False),  # Unsupported protocol
            ("", False),  # Empty string
            ("not-a-url", False),  # Invalid format
            ("http://", False),  # Incomplete
        ],
    )
    def test_is_valid_url(self, url: str, expected: bool) -> None:
        assert is_valid_url(url) == expected

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("example.com", "http://example.com"),
            ("http://example.com", "http://example.com"),
            ("https://example.com", "https://example.com"),
            ("", ""),
            ("http://localhost:8080", "http://localhost:8080"),
        ],
    )
    def test_normalize_url(self, url: str, expected: str) -> None:
        assert normalize_url(url) == expected

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("http://example.com", "example.com"),
            ("https://example.com/path", "example.com"),
            ("http://localhost:8080", "localhost:8080"),
            ("http://127.0.0.1", "127.0.0.1"),
            ("example.com", None),  # Invalid URL without protocol
            ("", None),
            ("not-a-url", None),
        ],
    )
    def test_extract_domain(self, url: str, expected: str | None) -> None:
        assert extract_domain(url) == expected
