"""Albums grid view for the music library."""
from __future__ import annotations
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame,
    QHBoxLayout, QSizePolicy, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QFont, QAction, QCursor

from src.backend.models import Album
from src.backend.services.interfaces import LibraryService


class AlbumCard(QFrame):
    """Individual album card widget."""

    clicked = Signal(Album)
    right_clicked = Signal(Album)

    def __init__(self, album: Album, parent=None):
        super().__init__(parent)
        self.album = album
        self.setObjectName("AlbumCard")
        self.setFixedSize(200, 260)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Artwork
        self.artwork_label = QLabel()
        self.artwork_label.setFixedSize(184, 184)
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artwork_label.setStyleSheet("""
            QLabel {
                background-color: #3a1828;
                border-radius: 6px;
                border: 1px solid #4a1d3a;
                color: #c94f7c;
            }
        """)
        self.artwork_label.setFont(QFont("Segoe UI", 32))
        self._load_artwork()

        # Album name
        self.name_label = QLabel(self.album.name)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.name_label.setStyleSheet("color: #f5e6eb; font-size: 13px; font-weight: 500;")
        self.name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))

        # Artist name
        self.artist_label = QLabel(self.album.artist)
        self.artist_label.setWordWrap(True)
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.artist_label.setStyleSheet("color: #a8879a; font-size: 11px;")

        layout.addWidget(self.artwork_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.artist_label)

    def _load_artwork(self) -> None:
        """Load album artwork from file or show placeholder."""
        if self.album.artwork_path:
            pixmap = QPixmap(self.album.artwork_path)
            if not pixmap.isNull():
                self.artwork_label.setPixmap(pixmap.scaled(
                    184, 184,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                ))
                return
        self.artwork_label.setText("♪")

    def mousePressEvent(self, event):
        """Handle mouse press for click detection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.album)
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.album)
        super().mousePressEvent(event)


class AlbumsView(QWidget):
    """Grid view for displaying all albums."""

    album_selected = Signal(Album)  # Emits album when clicked

    def __init__(
        self,
        library_service: LibraryService,
        playback_service=None,
        queue_service=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("AlbumsView")

        self.library_service = library_service
        self.queue_service = queue_service
        self.albums: List[Album] = []

        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        """Create the main container with scrollable grid."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(0)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #1a0d14; width: 8px; border: none;
            }
            QScrollBar::handle:vertical {
                background: #4a1d3a; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #c94f7c; }
        """)

        # Container widget for grid
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid_layout = QHBoxLayout(self.container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

        # Track cards for cleanup
        self._cards: List[AlbumCard] = []

    def refresh_data(self) -> None:
        """Load albums from backend and rebuild grid."""
        self.albums = self.library_service.get_all_albums()
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        """Clear and rebuild the album grid."""
        # Clear existing cards
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        # Clear grid layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create new cards
        self._cards = []
        for album in self.albums:
            card = AlbumCard(album)
            card.clicked.connect(self._on_album_clicked)
            card.right_clicked.connect(self._on_album_right_clicked)
            self.grid_layout.addWidget(card)
            self._cards.append(card)

        # Add stretch to keep cards left-aligned
        self.grid_layout.addStretch()

    @Slot()
    def _on_album_clicked(self, album: Album) -> None:
        """Handle album card click."""
        self.album_selected.emit(album)

    @Slot()
    def _on_album_right_clicked(self, album: Album) -> None:
        """Handle album card right-click - context menu."""
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

        play_action = QAction("Play Album", self)
        play_action.triggered.connect(lambda: self._play_album(album))
        menu.addAction(play_action)

        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self._add_album_to_queue(album))
        menu.addAction(add_queue_action)

        menu.addSeparator()

        add_playlist_action = QAction("Add to Playlist...", self)
        menu.addAction(add_playlist_action)

        menu.exec(QCursor.pos())

    def _play_album(self, album: Album) -> None:
        """Play all songs from the album."""
        songs = self.library_service.get_songs_by_album(album.id)
        if songs and self.queue_service:
            self.queue_service.clear_queue()
            for song in songs:
                self.queue_service.add_to_queue(song)
            self.queue_service.set_current_index(0)
            # The queue callback should trigger playback

    def _add_album_to_queue(self, album: Album) -> None:
        """Add all album songs to queue."""
        songs = self.library_service.get_songs_by_album(album.id)
        if songs and self.queue_service:
            for song in songs:
                self.queue_service.add_to_queue(song)

    def get_album_count(self) -> int:
        """Get total number of albums."""
        return len(self.albums)