"""Database connection manager for services."""
from __future__ import annotations
from sqlite3 import Connection
import src.backend.utils.database as db_util


def get_connection() -> Connection:
    """Get database connection from utility module."""
    return db_util.get_connection()


def init_database():
    """Initialize database schema."""
    db_util.init_database()


def close_connection():
    """Close database connection."""
    db_util.close_connection()


def reset_database():
    """Reset database (for testing)."""
    db_util.reset_database()