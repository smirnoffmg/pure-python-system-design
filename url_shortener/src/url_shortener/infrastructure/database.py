"""
Database connection management utilities.
"""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager


class DatabaseManager:
    """Manages database connections and initialization."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        """Get a database connection (for testing compatibility)."""
        return sqlite3.connect(self.db_path)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        """Initialize the database with required tables."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS url_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_url TEXT UNIQUE NOT NULL
                )
                """
            )
            conn.commit()
