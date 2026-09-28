"""Artists list view for the music library."""
from __future__ import annotations
from typing import List, Optional

from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor, QAction

from src.backend.models import Artist
from src.backend.services.interfaces import LibraryService


class ArtistsView(QWidget):
    """List view for displaying artists."""

    artist_selected = Signal(Artist)  # Emits artist when double-clicked

    def __init__(
        self,
        library_service: LibraryService,
        playback_service=None,
        queue_service=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ArtistsView")

        self.library_service = library_service
        self.queue_service = queue_service
        self.artists: List[Artist] = []

        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        """Create the main widget layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list.setAlternatingRowColors(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                color: #f5e6eb;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background: #4a1d3a;
            }
            QListWidget::item:selected {
                background: #c94f7c;
                color: white;
            }
        """)

        self.list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.list)
        self.setLayout(layout)

    def refresh_data(self) -> None:
        """Load artists from the backend and populate the list."""
        self.artists = self.library_service.get_all_artists()

        self.list.clear()
        for artist in self.artists:
            item = QListWidgetItem()
            # Main text: artist name
            item.setText(artist.name)
            # Subtitle as tooltip
            item.setToolTip(f"{artist.album_count} albums • {artist.song_count} songs")
            item.setData(Qt.ItemDataRole.UserRole, artist.id)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.list.addItem(item)

    @Slot()
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click - filter songs by this artist."""
        artist_id = item.data(Qt.ItemDataRole.UserRole)
        artist = next((a for a in self.artists if a.id == artist_id), None)
        if artist:
            self.artist_selected.emit(artist)

    @Slot()
    def _show_context_menu(self, pos) -> None:
        """Show right-click context menu."""
        item = self.list.itemAt(pos)
        if not item:
            return

        artist_id = item.data(Qt.ItemDataRole.UserRole)
        artist = next((a for a in self.artists if a.id == artist_id), None)
        if not artist:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2d1321;
                border: 1px solid #4a1d3a;
                border-radius: 6px;
                color: #f5e6eb;
            }
            QMenu::item { padding: 8px 24px; }
            QMenu::item:selected { background: #c94f7c; }
        """)

        play_action = QAction("Play Artist", self)
        play_action.triggered.connect(lambda: self._play_artist(artist))
        menu.addAction(play_action)

        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self._add_artist_to_queue(artist))
        menu.addAction(add_queue_action)

        menu.exec(QCursor.pos())

    def _play_artist(self, artist: Artist) -> None:
        """Play all songs by the artist."""
        songs = self.library_service.get_songs_by_artist(artist.id)
        if songs and self.queue_service:
            self.queue_service.clear_queue()
            for song in songs:
                self.queue_service.add_to_queue(song)
            self.queue_service.set_current_index(0)

    def _add_artist_to_queue(self, artist: Artist) -> None:
        """Add all artist songs to queue."""
        songs = self.library_service.get_songs_by_artist(artist.id)
        if songs and self.queue_service:
            for song in songs:
                self.queue_service.add_to_queue(song)

    def get_artist_count(self) -> int:
        """Get total number of artists."""
        return len(self.artists)

    def set_current_artist(self, index: int) -> None:
        """Navigate to a specific artist by index."""
        if 0 <= index < len(self.artists):
            self.list.setCurrentRow(index)

    def get_current_artist(self) -> Optional[Artist]:
        """Get the artist at the current selection."""
        item = self.list.currentItem()
        if item:
            artist_id = item.data(Qt.ItemDataRole.UserRole)
            return next((a for a in self.artists if a.id == artist_id), None)
        return None