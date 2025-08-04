"""
HTTP response serialization utilities.
"""

import json

from .types import HTTPResponse


class HTTPResponseSerializer:
    """
    Helper class to serialize HTTP responses.
    """

    @staticmethod
    def serialize(response: HTTPResponse) -> bytes:
        """Serialize HTTPResponse to bytes."""
        lines = [f"HTTP/1.1 {response.status_code} {response.status_message}"]

        headers = response.headers or {}
        body_str = HTTPResponseSerializer._serialize_body(response.body, headers)

        headers["Connection"] = "close"

        lines.extend(f"{key}: {value}" for key, value in headers.items())
        lines.append("")
        lines.append(body_str)

        return "\r\n".join(lines).encode()

    @staticmethod
    def _serialize_body(body: dict | None, headers: dict[str, str]) -> str:
        """Serialize response body and update headers accordingly."""
        if body is not None:
            body_str = json.dumps(body)
            headers["Content-Length"] = str(len(body_str))
            headers["Content-Type"] = "application/json"
            return body_str
        else:
            return ""
