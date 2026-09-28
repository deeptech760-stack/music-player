"""Search view for the music library."""
from __future__ import annotations
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont

from src.backend.services.interfaces import LibraryService
from src.backend.models import SearchResult, Song, Album, Artist, Playlist


class SearchView(QWidget):
    """Search view with real-time filtering across library."""

    play_song_requested = Signal(Song)

    def __init__(
        self,
        library_service: LibraryService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SearchView")
        self.library_service = library_service

        self._build_ui()
        self._connect_signals()

        # Debounce timer
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._perform_search)

    def _build_ui(self) -> None:
        """Create the search view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Search input
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs, albums, artists, playlists...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #2d1321;
                border: 1px solid #4a1d3a;
                border-radius: 6px;
                padding: 10px 16px;
                color: #f5e6eb;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #c94f7c;
            }
        """)

        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Results stack (different result types)
        self.results_stack = QStackedWidget()

        # Songs results
        from src.frontend.ui.songs_view import SongsView
        self.songs_results = SongsView(self.library_service, None, None)
        self.songs_results.play_song_requested.connect(self.play_song_requested.emit)
        self.results_stack.addWidget(self.songs_results)

        # Albums results
        from src.frontend.ui.albums_view import AlbumsView
        self.albums_results = AlbumsView(self.library_service, None, None)
        self.albums_results.album_selected.connect(self._on_album_selected)
        self.results_stack.addWidget(self.albums_results)

        # Artists results
        from src.frontend.ui.artists_view import ArtistsView
        self.artists_results = ArtistsView(self.library_service, None, None)
        self.artists_results.artist_selected.connect(self._on_artist_selected)
        self.results_stack.addWidget(self.artists_results)

        # Playlists results (placeholder for now)
        from PySide6.QtWidgets import QLabel
        playlists_placeholder = QLabel("Playlist search results\n(Not yet implemented)")
        playlists_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        playlists_placeholder.setProperty("secondary", True)
        self.results_stack.addWidget(playlists_placeholder)

        # Default to songs view
        self.results_stack.setCurrentIndex(0)
        layout.addWidget(self.results_stack, 1)

        # Result tabs
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(4)

        self.songs_tab = self._create_tab_button("Songs", 0, True)
        self.albums_tab = self._create_tab_button("Albums", 1, False)
        self.artists_tab = self._create_tab_button("Artists", 2, False)
        self.playlists_tab = self._create_tab_button("Playlists", 3, False)

        tabs_layout.addWidget(self.songs_tab)
        tabs_layout.addWidget(self.albums_tab)
        tabs_layout.addWidget(self.artists_tab)
        tabs_layout.addWidget(self.playlists_tab)
        tabs_layout.addStretch()

        layout.addLayout(tabs_layout)

    def _create_tab_button(self, text: str, index: int, checked: bool) -> QLabel:
        """Create a styled tab button."""
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #a8879a;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #f5e6eb;
                background: #4a1d3a;
            }
            QPushButton:checked {
                color: #c94f7c;
                background: #3a1828;
            }
        """)
        btn.clicked.connect(lambda: self._switch_results_tab(index))
        return btn

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self.search_input.textChanged.connect(self._on_search_text_changed)

    @Slot()
    def _on_search_text_changed(self, text: str) -> None:
        """Handle search input changes with debounce."""
        self._search_timer.start()

    @Slot()
    def _perform_search(self) -> None:
        """Execute the search query."""
        query = self.search_input.text().strip()
        if not query:
            self._clear_results()
            return

        try:
            results: SearchResult = self.library_service.search(query)
            self._display_results(results)
        except Exception:
            self._clear_results()

    def _display_results(self, results: SearchResult) -> None:
        """Display search results in the appropriate views."""
        # Update songs view
        self.songs_results._filtered_songs = results.songs
        self.songs_results._populate_table()

        # Update albums view
        self.albums_results.albums = results.albums
        self.albums_results._rebuild_grid()

        # Update artists view
        self.artists_results.artists = results.artists
        self.artists_results.refresh_data()

        # Switch to songs tab by default
        self._switch_results_tab(0)

    def _clear_results(self) -> None:
        """Clear all results."""
        self.songs_results._filtered_songs = []
        self.songs_results._populate_table()
        self.albums_results.albums = []
        self.albums_results._rebuild_grid()
        self.artists_results.artists = []
        self.artists_results.refresh_data()

    @Slot()
    def _switch_results_tab(self, index: int) -> None:
        """Switch between result types."""
        self.results_stack.setCurrentIndex(index)

        # Update tab buttons
        for i, btn in enumerate([self.songs_tab, self.albums_tab, self.artists_tab, self.playlists_tab]):
            btn.setChecked(i == index)

    @Slot()
    def _on_album_selected(self, album) -> None:
        """Handle album selection from search results."""
        # Switch to albums tab and scroll to album
        self._switch_results_tab(1)

    @Slot()
    def _on_artist_selected(self, artist) -> None:
        """Handle artist selection from search results."""
        self._switch_results_tab(2)