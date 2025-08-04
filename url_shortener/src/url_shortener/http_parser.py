"""
HTTP parsing utilities for the URL shortener service.
"""

from .logger import logger
from .types import HTTPRequest


class HTTPRequestParser:
    """
    Handles parsing of raw HTTP request data.
    """

    @staticmethod
    def parse(raw_data: bytes) -> HTTPRequest | None:
        """
        Parse raw HTTP request data into HTTPRequest object.

        Returns None if the request is incomplete or invalid.
        """
        try:
            header_part, _, body_part = raw_data.partition(b"\r\n\r\n")
            header_lines = header_part.decode().split("\r\n")

            if not header_lines:
                return None

            request_line = header_lines[0]
            if " " not in request_line:
                return None

            method, path, version = request_line.split(" ", 2)

            headers = HTTPRequestParser._parse_headers(header_lines[1:])

            # If no headers and no body, consider it incomplete
            if not headers and not body_part:
                return None

            body = HTTPRequestParser._parse_body(headers, body_part)
            if body is None:
                return None  # Incomplete request

            return HTTPRequest(method, path, version, headers, body)

        except Exception as e:
            logger.error(f"Failed to parse HTTP request: {e}")
            return None

    @staticmethod
    def _parse_headers(header_lines: list[str]) -> dict[str, str]:
        """Parse HTTP headers from header lines."""
        headers = {}
        for line in header_lines:
            if not line.strip() or ":" not in line:
                continue
            key, val = line.split(":", 1)
            headers[key.strip().lower()] = val.strip()
        return headers

    @staticmethod
    def _parse_body(headers: dict[str, str], body_part: bytes) -> str | None:
        """Parse HTTP body based on content length."""
        content_length = int(headers.get("content-length", 0))

        # If no content length, return empty string
        if content_length == 0:
            return ""

        # Check if full body is received
        if len(body_part) >= content_length:
            return body_part[:content_length].decode()
        else:
            # Incomplete request - need more data
            return None
