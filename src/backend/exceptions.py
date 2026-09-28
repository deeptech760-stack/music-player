"""Custom exceptions for the music player backend."""
from __future__ import annotations


class BackendError(Exception):
    """Base exception for backend errors."""
    pass


class DatabaseError(BackendError):
    """Database-related errors."""
    pass


class PlaybackError(BackendError):
    """Audio playback errors."""
    pass


class LibraryError(BackendError):
    """Library scanning/management errors."""
    pass


class MetadataError(BackendError):
    """Metadata extraction errors."""
    pass


class SettingsError(BackendError):
    """Settings persistence errors."""
    pass


class QueueError(BackendError):
    """Queue management errors."""
    pass


class PlaylistError(BackendError):
    """Playlist management errors."""
    pass