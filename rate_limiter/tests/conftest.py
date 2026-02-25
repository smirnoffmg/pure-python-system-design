from datetime import datetime
from unittest.mock import MagicMock


def make_mock_datetime(initial: datetime) -> MagicMock:
    """Create a mock datetime class whose .now() returns a controllable value.

    Usage in tests:
        mock_dt = make_mock_datetime(datetime(2025, 1, 1))
        with patch("src.strategies.token_bucket.datetime", mock_dt):
            ...
            mock_dt.now.return_value = datetime(2025, 1, 1, 0, 0, 5)  # advance 5s
    """
    mock_dt = MagicMock(wraps=datetime)
    mock_dt.now.return_value = initial
    return mock_dt
