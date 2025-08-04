"""
URL utility functions for the infrastructure layer.
"""

import re
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.

    Args:
        url (str): The URL string to validate

    Returns:
        bool: True if valid URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    # Basic URL pattern validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return bool(url_pattern.match(url))


def normalize_url(url: str) -> str:
    """
    Normalize URL by adding protocol if missing.

    Args:
        url (str): The URL to normalize

    Returns:
        str: Normalized URL with protocol
    """
    if not url:
        return url

    # If URL doesn't start with protocol, assume http
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    return url


def extract_domain(url: str) -> str | None:
    """
    Extract domain from URL.

    Args:
        url (str): The URL to extract domain from

    Returns:
        str | None: Domain name or None if invalid
    """
    if not url:
        return None

    # First validate the URL
    if not is_valid_url(url):
        return None

    try:
        # Normalize URL first
        normalized = normalize_url(url)
        parsed = urlparse(normalized)

        # Check if we have a valid netloc (domain)
        if not parsed.netloc:
            return None

        return parsed.netloc
    except Exception:
        return None
