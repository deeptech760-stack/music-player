"""Data models for the music player application."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Any, Dict


class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class RepeatMode(Enum):
    """Repeat mode enumeration."""
    OFF = "off"
    ONE = "one"
    ALL = "all"


@dataclass
class Song:
    """Song data model."""
    id: int
    path: str
    title: str
    artist: str
    album: str
    album_artist: str
    genre: str
    year: Optional[int]
    track_number: Optional[int]
    disc_number: Optional[int]
    duration: float
    bitrate: int
    sample_rate: int
    channels: int
    file_size: int
    date_added: datetime
    artwork_path: Optional[str] = None


@dataclass
class Album:
    """Album data model."""
    id: int
    name: str
    artist: str
    year: Optional[int]
    genre: str
    song_count: int
    total_duration: float
    artwork_path: Optional[str] = None


@dataclass
class Artist:
    """Artist data model."""
    id: int
    name: str
    album_count: int
    song_count: int


@dataclass
class Genre:
    """Genre data model."""
    id: int
    name: str
    song_count: int


@dataclass
class Playlist:
    """Playlist data model."""
    id: int
    name: str
    song_count: int
    total_duration: float
    created_at: datetime
    updated_at: datetime


@dataclass
class QueueItem:
    """Queue item data model."""
    index: int
    song: Song
    added_at: datetime


@dataclass
class ScanResult:
    """Library scan result."""
    files_scanned: int
    files_added: int
    files_updated: int
    files_removed: int
    errors: List[str]
    duration_seconds: float


@dataclass
class SearchResult:
    """Search result containing search hits."""
    songs: List[Song]
    albums: List[Album]
    artists: List[Artist]
    playlists: List[Playlist]


# Settings default values
DEFAULT_SETTINGS: Dict[str, Any] = {
    "library_paths": [],
    "volume": 0.7,
    "shuffle": False,
    "repeat_mode": RepeatMode.OFF.value,
    "theme": "dark",
    "minimize_to_tray": True,
    "start_minimized": False,
    "auto_scan_on_startup": True,
}


def song_from_dict(data: Dict[str, Any]) -> Optional[Song]:
    """Create Song from dictionary (can be dict response from DB)."""
    try:
        # Handle null values for optional fields
        year = data.get("year")
        year = int(year) if year and year is not None else year
        
        track_number = data.get("track_number")
        track_number = int(track_number) if track_number and track_number is not None else None
        
        disc_number = data.get("disc_number")
        disc_number = int(disc_number) if disc_number and disc_number is not None else None
        
        # Handle artwork_path which might be None or a path in the dict
        artwork_path = data.get("artwork_path") or None
        
        return Song(
            id=data.get("id", 0),
            path=data.get("path", ""),
            title=data.get("title", ""),
            artist=data.get("artist", ""),
            album=data.get("album", ""),
            album_artist=data.get("album_artist", ""),
            genre=data.get("genre", ""),
            year=year,
            track_number=track_number,
            disc_number=disc_number,
            duration=data.get("duration", 0),
            bitrate=data.get("bitrate", 0),
            sample_rate=data.get("sample_rate", 0),
            channels=data.get("channels", 0),
            file_size=data.get("file_size", 0),
            date_added=datetime.fromisoformat(data.get("date_added", "1970-01-01")) if isinstance(data.get("date_added"), str) else None,
            artwork_path=artwork_path,
        )
    except Exception:
        return None


def album_from_dict(data: Dict[str, Any]) -> Optional[Album]:
    """Create Album from dictionary."""
    try:
        return Album(
            id=data.get("id", 0),
            name=data.get("name", ""),
            artist=data.get("artist", ""),
            year=data.get("year"),
            genre=data.get("genre", ""),
            song_count=data.get("song_count", 0),
            total_duration=data.get("total_duration", 0.0),
            artwork_path=data.get("artwork_path"),
        )
    except Exception:
        return None


def artist_from_dict(data: Dict[str, Any]) -> Optional[Artist]:
    """Create Artist from dictionary."""
    try:
        return Artist(
            id=data.get("id", 0),
            name=data.get("name", ""),
            album_count=data.get("album_count", 0),
            song_count=data.get("song_count", 0),
        )
    except Exception:
        return None


def genre_from_dict(data: Dict[str, Any]) -> Optional[Genre]:
    """Create Genre from dictionary."""
    try:
        return Genre(
            id=data.get("id", 0),
            name=data.get("name", ""),
            song_count=data.get("song_count", 0),
        )
    except Exception:
        return None


def playlist_from_dict(data: Dict[str, Any]) -> Optional[Playlist]:
    """Create Playlist from dictionary."""
    try:
        return Playlist(
            id=data.get("id", 0),
            name=data.get("name", ""),
            song_count=data.get("song_count", 0),
            total_duration=data.get("total_duration", 0.0),
            created_at=datetime.fromisoformat(data.get("created_at", "1970-01-01")) if isinstance(data.get("created_at"), str) else None,
            updated_at=datetime.fromisoformat(data.get("updated_at", "1970-01-01")) if isinstance(data.get("updated_at"), str) else None,
        )
    except Exception:
        return None


def queue_item_from_dict(data: Dict[str, Any]) -> Optional[QueueItem]:
    """Create QueueItem from dictionary."""
    try:
        return QueueItem(
            index=data.get("index", 0),
            song=song_from_dict(data.get("song")),
            added_at=datetime.fromisoformat(data.get("added_at", "1970-01-01")) if isinstance(data.get("added_at"), str) else None,
        )
    except Exception:
        return None


def get_empty_song() -> Song:
    """Return empty Song for queue item placeholder."""
    return Song(
        id=0,
        path="",
        title="",
        artist="",
        album="",
        album_artist="",
        genre="",
        year=None,
        track_number=None,
        disc_number=None,
        duration=0,
        bitrate=0,
        sample_rate=0,
        channels=0,
        file_size=0,
        date_added=datetime.now(),
        artwork_path=None,
    )


def get_empty_album() -> Album:
    """Return empty Album."""
    return Album(
        id=0,
        name="",
        artist="",
        year=None,
        genre="",
        song_count=0,
        total_duration=0.0,
        artwork_path=None,
    )


def get_empty_artist() -> Artist:
    """Return empty Artist."""
    return Artist(
        id=0,
        name="",
        album_count=0,
        song_count=0,
    )


def get_empty_genre() -> Genre:
    """Return empty Genre."""
    return Genre(
        id=0,
        name="",
        song_count=0,
    )


def get_empty_playlist() -> Playlist:
    """Return empty Playlist."""
    return Playlist(
        id=0,
        name="",
        song_count=0,
        total_duration=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
