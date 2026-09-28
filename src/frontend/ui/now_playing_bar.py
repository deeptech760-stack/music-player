import sys
import os
from typing import Optional, Tuple, Dict
from math import floor

class NowPlayingBar(QFrame):
    """
    Bottom status bar for current track.
    """

    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    next_clicked = Signal()
    prev_clicked = Signal()
    seek_requested = Signal(float)
    volume_changed = Signal(float)
    state_changed = Signal(str)
    track_updated = Signal(dict)
    artwork_updated = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.track_info = {"title": "No Track", "artist": "Unknown Artist", "album": "Unknown Album"}
        self.position = 0.0
        self.duration = 0.0
        self.state = "stopped"
        
        self.setMinimumWidth(480)
        self.setMinimumHeight(65)

    def set_track_info(self, title: str, artist: str, album: str, artwork_path: str):
        """
        Set current track info.
        """
        pass

    def set_position(self, position: float):
        """
        Set current playback position.
        """
        pass

    def set_duration(self, duration: float):
        """
        Set current track duration.
        """
        pass

    def set_state(self, state: str):
        """
        Set playback state.
        """
        pass

    def paintEvent(self, event):
        """
        Draw now playing bar with artwork placeholder, metadata, controls.
        """
        if not self.isVisible():
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.Smoothed, True)
        
        rect = self.rect()
        fill_color = QColor("#150a18")
        painter.fillRect(rect, fill_color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()