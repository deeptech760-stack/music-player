"""QueueService implementation for playback queue management."""
from __future__ import annotations
import threading
from datetime import datetime
from typing import Optional, List, Callable

from src.backend.services.interfaces import QueueService, QueueChangedCallback
from src.backend.models import Song, QueueItem
from src.backend.services.database import get_connection


class QueueServiceImpl(QueueService):
    """Implementation of QueueService for playback queue management."""

    def __init__(self) -> None:
        """Initialize queue service."""
        self.db = get_connection()
        self._queue: List[QueueItem] = []
        self._lock = threading.RLock()  # RLock is reentrant - same thread can acquire multiple times
        self._queue_callbacks: List[QueueChangedCallback] = []
        self._repeat_mode = "off"  # off, one, all
        self._shuffle = False

    def get_queue(self) -> List[QueueItem]:
        """Get current queue."""
        with self._lock:
            return list(self._queue)

    def add_to_queue(self, song: Song, position: Optional[int] = None) -> None:
        """Add song to queue at position (or end if None)."""
        with self._lock:
            if position is None:
                position = len(self._queue)
            self._queue.insert(position, QueueItem(
                index=position,
                song=song,
                added_at=datetime.now(),
            ))
            self._notify_callbacks()

    def remove_from_queue(self, index: int) -> None:
        """Remove item at index from queue."""
        with self._lock:
            if 0 <= index < len(self._queue):
                self._queue.pop(index)
                self._reindex_queue()
                self._notify_callbacks()

    def move_in_queue(self, from_index: int, to_index: int) -> None:
        """Move queue item from one position to another."""
        with self._lock:
            if 0 <= from_index < len(self._queue) and 0 <= to_index < len(self._queue):
                item = self._queue.pop(from_index)
                self._queue.insert(to_index, item)
                self._reindex_queue()
                self._notify_callbacks()

    def clear_queue(self) -> None:
        """Clear the entire queue."""
        with self._lock:
            self._queue = []
            self._notify_callbacks()

    def set_current_index(self, index: int) -> None:
        """Set the currently playing index."""
        with self._lock:
            if 0 <= index < len(self._queue):
                self._queue[index].index = index
                self._notify_callbacks()

    def get_current_index(self) -> int:
        """Get the currently playing index."""
        with self._lock:
            if self._queue:
                return self._queue[0].index
            return -1

    def _reindex_queue(self) -> None:
        """Reindex all queue items."""
        for i, item in enumerate(self._queue):
            item.index = i

    def on_queue_changed(self, callback: QueueChangedCallback) -> None:
        """Register callback for queue changes."""
        if callback not in self._queue_callbacks:
            self._queue_callbacks.append(callback)

    def remove_queue_callback(self, callback: QueueChangedCallback) -> None:
        """Remove queue callback."""
        if callback in self._queue_callbacks:
            self._queue_callbacks.remove(callback)

    def _notify_callbacks(self) -> None:
        """Notify all queue change callbacks."""
        # Get snapshot while holding lock, then release before calling callbacks
        with self._lock:
            queue_snapshot = list(self._queue)
        for callback in self._queue_callbacks:
            try:
                callback()
            except Exception:
                import logging
                logging.error(f"Queue callback failed: {callback}")

    def get_repeat_mode(self) -> str:
        """Get current repeat mode."""
        with self._lock:
            return self._repeat_mode

    def set_repeat_mode(self, mode: str) -> None:
        """Set repeat mode (off, one, all)."""
        with self._lock:
            if mode in ("off", "one", "all"):
                self._repeat_mode = mode

    def get_shuffle(self) -> bool:
        """Get shuffle state."""
        with self._lock:
            return self._shuffle

    def set_shuffle(self, enabled: bool) -> None:
        """Set shuffle state."""
        with self._lock:
            self._shuffle = enabled



