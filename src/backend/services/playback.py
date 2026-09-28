"""PlaybackService implementation using python-vlc."""
from __future__ import annotations
from typing import Optional, List
import logging
import threading
import queue
import time

from src.backend.services.interfaces import PlaybackService, PositionCallback, StateCallback, TrackFinishedCallback
from src.backend.services.database import get_connection
from src.backend.models import Song, PlaybackState, QueueItem
from src.backend.exceptions import BackendError
import vlc


logger = logging.getLogger(__name__)


class PlaybackServiceImpl(PlaybackService):
    """Implementation of PlaybackService using python-vlc."""

    # VLC instance - Singleton pattern
    _instance: Optional[vlc.Instance] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize playback service."""
        self.db = get_connection()
        self._instance: Optional[vlc.Instance] = None
        self._player: Optional[vlc.MediaPlayer] = None
        self._position_callbacks: List[PositionCallback] = []
        self._state_callbacks: List[StateCallback] = []
        self._finished_callbacks: List[TrackFinishedCallback] = []
        self._current_position_subscribers: List[PositionCallback] = []
        self._position_queue: queue.Queue = queue.Queue(maxsize=100)
        self._position_thread: Optional[threading.Thread] = None
        self._running: bool = False

    def _ensure_instance(self) -> None:
        """Ensure VLC instance and player exist."""
        if self._instance is None:
            self._instance = vlc.Instance('--no-video')
        if self._player is None:
            self._player = self._instance.media_player_new()
            # Set up event manager
            event_manager = self._player.event_manager()
            event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

    def _ensure_player(self) -> None:
        """Ensure player exists."""
        self._ensure_instance()

    def play(self, song: Song) -> None:
        """Start playing a song. Non-blocking for Qt GUI."""
        try:
            self._ensure_instance()
            media = self._instance.media_new_path(song.path)
            self._player.set_media(media)
            self._player.play()
            self._start_position_polling()
        except (ImportError, AttributeError) as e:
            logger.error(f"VLC import/attribute error: {e}")
            raise BackendError("VLC library not available")
        except Exception as e:
            logger.error(f"Play failed: {e}")
            raise BackendError(f"Failed to play song: {e}")

    def _on_end_reached(self, event) -> None:
        """Handle track end reached event. Queue for safe callback execution."""
        try:
            self._position_queue.put_nowait(('finished', None))
        except queue.Full:
            # Queue full, try to flush one item
            try:
                self._position_queue.get_nowait()
            except queue.Empty:
                pass

    def _start_position_polling(self) -> None:
        """Start position polling thread with daemon flag."""
        if self._position_thread is not None and self._position_thread.is_alive():
            return
        self._running = True
        self._position_thread = threading.Thread(
            target=self._poll_position, daemon=True, name="PlaybackPositionPoller"
        )
        self._position_thread.start()

    def _stop_position_polling(self) -> None:
        """Stop the position polling thread."""
        self._running = False
        if self._position_thread is not None:
            self._position_thread.join(timeout=1.0)
            self._position_thread = None

    def _poll_position(self) -> None:
        """Poll position from VLC player in daemon background thread."""
        while self._running:
            try:
                if self._player and self._player.is_playing():
                    pos = self._player.get_position()
                    try:
                        self._position_queue.put_nowait(('position', pos))
                    except queue.Full:
                        pass  # Drop if queue full, next poll will update
                else:
                    try:
                        self._position_queue.put_nowait(('position', 0.0))
                    except queue.Full:
                        pass
            except Exception:
                # Ignore VLC errors, continue polling
                pass
            try:
                time.sleep(0.2)
            except InterruptedError:
                continue

    def process_events(self) -> None:
        """Process queued events and invoke callbacks. Call from main thread."""
        try:
            while not self._position_queue.empty():
                msg_type, data = self._position_queue.get_nowait()
                if msg_type == 'position':
                    for cb in self._position_callbacks:
                        try:
                            cb(data)
                        except Exception as e:
                            logger.error(f"Position callback failed: {e}")
                elif msg_type == 'finished':
                    for cb in self._finished_callbacks:
                        try:
                            cb()
                        except Exception as e:
                            logger.error(f"Track finished callback failed: {e}")
                elif msg_type == 'error':
                    # Could emit error state - TODO: implement error handling
                    pass
        except queue.Empty:
            pass
    
    def pause(self) -> None:
        """Pause playback."""
        self._ensure_player()
        if self._player:
            self._player.pause()

    def resume(self) -> None:
        """Resume paused playback."""
        self._ensure_player()
        if self._player:
            self._player.play()

    def stop(self) -> None:
        """Stop playback."""
        self._ensure_player()
        if self._player:
            self._player.stop()
            self._stop_position_polling()
            # Create new media player after stop for next song
            self._player = self._instance.media_player_new()
            # Re-attach event handler
            event_manager = self._player.event_manager()
            event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

    def seek(self, position: float) -> None:
        """Seek to position (0.0-1.0)."""
        self._ensure_player()
        if self._player:
            self._player.set_position(position)

    def set_volume(self, volume: float) -> None:
        """Set volume (0.0-1.0)."""
        self._ensure_player()
        if self._player:
            self._player.audio_set_volume(int(volume * 100))

    def get_position(self) -> float:
        """Get current playback position (0.0-1.0)."""
        if not self._player:
            return 0.0
        return self._player.get_position()

    def get_duration(self) -> float:
        """Get current track duration in seconds."""
        if self._player:
            return self._player.get_length() / 1000.0  # ms to seconds
        return 0.0

    def get_state(self) -> PlaybackState:
        """Get current playback state."""
        if not self._player:
            return PlaybackState.STOPPED
        
        state_enum = self._player.get_state()
        if state_enum == vlc.State.Playing:
            return PlaybackState.PLAYING
        elif state_enum == vlc.State.Paused:
            return PlaybackState.PAUSED
        else:
            return PlaybackState.STOPPED
        
        return PlaybackState.STOPPED

    def on_position_changed(self, callback: PositionCallback) -> None:
        """Register callback for position updates."""
        self._position_callbacks.append(callback)
        # Call with current position if available
        if self._player:
            duration = self._player.get_length()
            if duration > 0:
                callback(self._player.get_position() / duration)

    def on_state_changed(self, callback: StateCallback) -> None:
        """Register callback for state changes."""
        self._state_callbacks.append(callback)

    def on_track_finished(self, callback: TrackFinishedCallback) -> None:
        """Register callback for track end."""
        self._finished_callbacks.append(callback)

    def remove_position_callback(self, callback: PositionCallback) -> None:
        """Remove position callback."""
        if callback in self._position_callbacks:
            self._position_callbacks.remove(callback)
            if callback in self._current_position_subscribers:
                self._current_position_subscribers.remove(callback)

    def remove_state_callback(self, callback: StateCallback) -> None:
        """Remove state callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def remove_track_finished_callback(self, callback: TrackFinishedCallback) -> None:
        """Remove track finished callback."""
        if callback in self._finished_callbacks:
            self._finished_callbacks.remove(callback)

    # Sentinel for current position subscribers
    _current_position_subscribers = []


def load_entry_point():
    """Load playback service entry point."""
    from src.backend.services.library import LibraryServiceImpl
    from src.backend.services.playlist import PlaylistServiceImpl
    from src.backend.services.queue import QueueServiceImpl
    from src.backend.services.settings import SettingsServiceImpl
    return {
        "PlaybackServiceImpl": PlaybackServiceImpl,
        "LibraryServiceImpl": LibraryServiceImpl,
        "PlaylistServiceImpl": PlaylistServiceImpl,
        "QueueServiceImpl": QueueServiceImpl,
        "SettingsServiceImpl": SettingsServiceImpl,
    }


def createPlaybackService() -> PlaybackService:
    """Create playback service instance."""
    return PlaybackServiceImpl()


def load_entry_points():
    """Load all entry points."""
    return load_entry_point()
