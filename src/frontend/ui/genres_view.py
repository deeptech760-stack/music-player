"""Genres list view for the music library."""
from __future__ import annotations
from typing import List, Optional

from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor, QAction

from src.backend.models import Genre
from src.backend.services.interfaces import LibraryService


class GenresView(QWidget):
    """List view for displaying genres."""

    genre_selected = Signal(Genre)  # Emits genre when double-clicked

    def __init__(
        self,
        library_service: LibraryService,
        playback_service=None,
        queue_service=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("GenresView")

        self.library_service = library_service
        self.queue_service = queue_service
        self.genres: List[Genre] = []

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
        """Load genres from the backend and populate the list."""
        self.genres = self.library_service.get_all_genres()

        self.list.clear()
        for genre in self.genres:
            item = QListWidgetItem()
            item.setText(genre.name)
            item.setToolTip(f"{genre.song_count} songs")
            item.setData(Qt.ItemDataRole.UserRole, genre.id)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.list.addItem(item)

    @Slot()
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click - filter songs by this genre."""
        genre_id = item.data(Qt.ItemDataRole.UserRole)
        genre = next((g for g in self.genres if g.id == genre_id), None)
        if genre:
            self.genre_selected.emit(genre)

    @Slot()
    def _show_context_menu(self, pos) -> None:
        """Show right-click context menu."""
        item = self.list.itemAt(pos)
        if not item:
            return

        genre_id = item.data(Qt.ItemDataRole.UserRole)
        genre = next((g for g in self.genres if g.id == genre_id), None)
        if not genre:
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

        play_action = QAction("Play Genre", self)
        play_action.triggered.connect(lambda: self._play_genre(genre))
        menu.addAction(play_action)

        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self._add_genre_to_queue(genre))
        menu.addAction(add_queue_action)

        menu.exec(QCursor.pos())

    def _play_genre(self, genre: Genre) -> None:
        """Play all songs in the genre."""
        songs = self.library_service.get_songs_by_genre(genre.id)
        if songs and self.queue_service:
            self.queue_service.clear_queue()
            for song in songs:
                self.queue_service.add_to_queue(song)
            self.queue_service.set_current_index(0)

    def _add_genre_to_queue(self, genre: Genre) -> None:
        """Add all genre songs to queue."""
        songs = self.library_service.get_songs_by_genre(genre.id)
        if songs and self.queue_service:
            for song in songs:
                self.queue_service.add_to_queue(song)

    def get_genre_count(self) -> int:
        """Get total number of genres."""
        return len(self.genres)

    def set_current_genre(self, index: int) -> None:
        """Navigate to a specific genre by index."""
        if 0 <= index < len(self.genres):
            self.list.setCurrentRow(index)

    def get_current_genre(self) -> Optional[Genre]:
        """Get the genre at the current selection."""
        item = self.list.currentItem()
        if item:
            genre_id = item.data(Qt.ItemDataRole.UserRole)
            return next((g for g in self.genres if g.id == genre_id), None)
        return None