"""Service interfaces (abstract base classes) for the music player backend."""
from __future__ import annotations
from typing import Optional, List, Callable, Any, Dict, Tuple
from abc import ABC, abstractmethod
from src.backend.models import (
    Song, Album, Artist, Genre, Playlist, QueueItem,
    ScanResult, SearchResult, PlaybackState
)

Callback = Tuple[Callable, Callable]

# Callback type aliases for PlaybackService
PositionCallback = Callable[[float], None]
StateCallback = Callable[[PlaybackState], None]
TrackFinishedCallback = Callable[[], None]
QueueChangedCallback = Callable[[], None]


class LibraryService(ABC):
    """Interface for library management and querying."""

    @abstractmethod
    def scan_library(self, paths: List[str]) -> ScanResult:
        """Scan library paths for audio files."""
        pass

    @abstractmethod
    def get_all_songs(self) -> List[Song]:
        """Get all songs in library."""
        pass

    @abstractmethod
    def get_all_albums(self) -> List[Album]:
        """Get all albums in library."""
        pass

    @abstractmethod
    def get_all_artists(self) -> List[Artist]:
        """Get all artists in library."""
        pass

    @abstractmethod
    def get_all_genres(self) -> List[Genre]:
        """Get all genres in library."""
        pass

    @abstractmethod
    def get_songs_by_album(self, album_id: int) -> List[Song]:
        """Get songs belonging to an album."""
        pass

    @abstractmethod
    def get_songs_by_artist(self, artist_id: int) -> List[Song]:
        """Get songs by an artist."""
        pass

    @abstractmethod
    def get_songs_by_genre(self, genre_id: int) -> List[Song]:
        """Get songs in a genre."""
        pass

    @abstractmethod
    def search(self, query: str) -> SearchResult:
        """Search library by query string."""
        pass

    @abstractmethod
    def get_song_by_id(self, song_id: int) -> Optional[Song]:
        """Get a song by its ID."""
        pass

    @abstractmethod
    def get_album_by_id(self, album_id: int) -> Optional[Album]:
        """Get an album by its ID."""
        pass

    @abstractmethod
    def get_artist_by_id(self, artist_id: int) -> Optional[Artist]:
        """Get an artist by its ID."""
        pass


class PlaybackService(ABC):
    """Interface for audio playback control."""

    @abstractmethod
    def play(self, song: Song) -> None:
        """Start playing a song."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause playback."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume paused playback."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop playback."""
        pass

    @abstractmethod
    def seek(self, position: float) -> None:
        """Seek to position (0.0-1.0)."""
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """Set volume (0.0-1.0)."""
        pass

    @abstractmethod
    def get_position(self) -> float:
        """Get current playback position (0.0-1.0)."""
        pass

    @abstractmethod
    def get_duration(self) -> float:
        """Get current track duration in seconds."""
        pass

    @abstractmethod
    def get_state(self) -> PlaybackState:
        """Get current playback state."""
        pass

    @abstractmethod
    def on_position_changed(self, callback: Callable[[float], None]) -> None:
        """Register callback for position updates."""
        pass

    @abstractmethod
    def on_state_changed(self, callback: Callable[[PlaybackState], None]) -> None:
        """Register callback for state changes."""
        pass

    @abstractmethod
    def on_track_finished(self, callback: Callable[[], None]) -> None:
        """Register callback for track end."""
        pass

    @abstractmethod
    def remove_position_callback(self, callback: Callable[[float], None]) -> None:
        """Remove position callback."""
        pass

    @abstractmethod
    def remove_state_callback(self, callback: Callable[[PlaybackState], None]) -> None:
        """Remove state callback."""
        pass

    @abstractmethod
    def remove_track_finished_callback(self, callback: Callable[[], None]) -> None:
        """Remove track finished callback."""
        pass


class QueueService(ABC):
    """Interface for playback queue management."""

    @abstractmethod
    def get_queue(self) -> List[QueueItem]:
        """Get current queue."""
        pass

    @abstractmethod
    def add_to_queue(self, song: Song, position: Optional[int] = None) -> None:
        """Add song to queue at position (or end if None)."""
        pass

    @abstractmethod
    def remove_from_queue(self, index: int) -> None:
        """Remove item at index from queue."""
        pass

    @abstractmethod
    def move_in_queue(self, from_index: int, to_index: int) -> None:
        """Move queue item from one position to another."""
        pass

    @abstractmethod
    def clear_queue(self) -> None:
        """Clear the entire queue."""
        pass

    @abstractmethod
    def set_current_index(self, index: int) -> None:
        """Set the currently playing index."""
        pass

    @abstractmethod
    def get_current_index(self) -> int:
        """Get the currently playing index."""
        pass

    @abstractmethod
    def on_queue_changed(self, callback: Callable[[], None]) -> None:
        """Register callback for queue changes."""
        pass

    @abstractmethod
    def remove_queue_callback(self, callback: Callable[[], None]) -> None:
        """Remove queue callback."""
        pass

    @abstractmethod
    def get_repeat_mode(self) -> str:
        """Get current repeat mode."""
        pass

    @abstractmethod
    def set_repeat_mode(self, mode: str) -> None:
        """Set repeat mode."""
        pass

    @abstractmethod
    def get_shuffle(self) -> bool:
        """Get shuffle state."""
        pass

    @abstractmethod
    def set_shuffle(self, enabled: bool) -> None:
        """Set shuffle state."""
        pass


class PlaylistService(ABC):
    """Interface for playlist management."""

    @abstractmethod
    def create_playlist(self, name: str) -> Playlist:
        """Create a new playlist."""
        pass

    @abstractmethod
    def delete_playlist(self, playlist_id: int) -> None:
        """Delete a playlist."""
        pass

    @abstractmethod
    def rename_playlist(self, playlist_id: int, name: str) -> None:
        """Rename a playlist."""
        pass

    @abstractmethod
    def get_all_playlists(self) -> List[Playlist]:
        """Get all playlists."""
        pass

    @abstractmethod
    def get_playlist(self, playlist_id: int) -> Playlist:
        """Get a playlist by ID."""
        pass

    @abstractmethod
    def get_playlist_songs(self, playlist_id: int) -> List[Song]:
        """Get songs in a playlist."""
        pass

    @abstractmethod
    def add_to_playlist(self, playlist_id: int, song: Song) -> None:
        """Add song to playlist."""
        pass

    @abstractmethod
    def remove_from_playlist(self, playlist_id: int, song_id: int) -> None:
        """Remove song from playlist."""
        pass

    @abstractmethod
    def reorder_playlist(self, playlist_id: int, from_index: int, to_index: int) -> None:
        """Reorder songs in playlist."""
        pass


class SettingsService(ABC):
    """Interface for settings persistence."""

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get a setting value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        pass

    @abstractmethod
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        pass