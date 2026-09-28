"""Settings service implementation for persistent settings management."""
from __future__ import annotations
import json
import logging
from typing import Any, Dict, Optional
import sqlite3

from src.backend.models import DEFAULT_SETTINGS
from src.backend.services.database import get_connection, close_connection

logger = logging.getLogger(__name__)


class SettingsServiceImpl:
    """Implementation of SettingsService for SQLite persistence."""

    def __init__(self):
        """Initialize the settings service."""
        self._conn: Optional[sqlite3.Connection] = get_connection()

    def get(self, key: str) -> Any:
        """Get a setting value with type coercion.
        
        Args:
            key: Setting key name
            
        Returns:
            Setting value as bool, int, float, list, or dict, or default if not found
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()

        if row:
            value_str = row[0]
            try:
                # Try JSON parsing first
                value = json.loads(value_str)
                
                # Type coercion - JSON already handles these types correctly
                return value
            except (json.JSONDecodeError, TypeError, ValueError):
                # Return as-is if not JSON serializable
                return value_str
        else:
            # Return default value if key not found
            return DEFAULT_SETTINGS.get(key, None)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value with JSON serialization.
        
        Args:
            key: Setting key name
            value: Any value to store (will be JSON serialized)
        """
        try:
            # Serialize value to JSON
            value_str = json.dumps(value)
            
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value_str)
            )
            self._conn.commit()
        except (sqlite3.Error, TypeError) as e:
            logger.error(f"Failed to set setting {key}: {e}")
            raise

    def get_all(self) -> Dict[str, Any]:
        """Get all settings with defaults applied.
        
        Returns:
            Dictionary of all settings with defaults for missing keys
        """
        cursor = self._conn.cursor()
        cursor.execute("SELECT key, value FROM settings ORDER BY key")
        rows = cursor.fetchall()
        
        settings_dict = {}
        for key, value_str in rows:
            # Convert bytes key to string if needed
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            try:
                # Try JSON parsing
                value = json.loads(value_str)
                settings_dict[key] = value
            except (json.JSONDecodeError, TypeError, ValueError):
                # Return as-is if not JSON serializable
                settings_dict[key] = value_str
        
        # Apply defaults for missing keys
        for key, default_value in DEFAULT_SETTINGS.items():
            if key not in settings_dict:
                settings_dict[key] = default_value
        
        return settings_dict

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values.
        
        Deletes existing settings and inserts defaults from DEFAULT_SETTINGS.
        """
        cursor = self._conn.cursor()
        
        # Delete all existing settings
        cursor.execute("DELETE FROM settings")
        
        # Clear any sqlite auto-increment counter
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'settings'")
        
        # Insert default settings
        for key, value in DEFAULT_SETTINGS.items():
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
        
        self._conn.commit()
        logger.info("Settings reset to defaults")
