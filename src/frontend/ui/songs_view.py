"""Songs table view for the music library."""
from __future__ import annotations
from typing import List, Optional

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QVBoxLayout, QWidget, QMenu, QHeaderView
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor, QAction

from src.backend.models import Song
from src.backend.services.interfaces import LibraryService, PlaybackService


class SongsView(QWidget):
    """Table view for displaying all songs with filtering capabilities."""

    # Signal emitted when a song should be played
    play_song_requested = Signal(Song)

    def __init__(
        self,
        library_service: LibraryService,
        playback_service: PlaybackService,
        queue_service=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SongsView")

        self.library_service = library_service
        self.playback_service = playback_service
        self.queue_service = queue_service

        self._all_songs: List[Song] = []
        self._filtered_songs: List[Song] = []
        self._current_filter = None  # ('album', id) or ('artist', id) or ('genre', id)

        self._build_ui()
        self._setup_table()
        self.refresh_data()

    def _build_ui(self) -> None:
        """Create the main container layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        self.setLayout(layout)

    def _setup_table(self) -> None:
        """Initialize QTableWidget with proper configuration."""
        self.table = QTableWidget()
        self.table.setObjectName("SongsTable")

        # 6 columns: #, Title, Artist, Album, Duration, Year
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "#", "Title", "Artist", "Album", "Duration", "Year"
        ])

        # Hide vertical header (row numbers)
        self.table.verticalHeader().setVisible(False)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Artist
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Album
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Duration
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Year

        self.table.setColumnWidth(0, 50)   # #
        self.table.setColumnWidth(4, 80)   # Duration
        self.table.setColumnWidth(5, 60)   # Year

        header.setStretchLastSection(False)

        # Behavior
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)

        # Signals
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        self.layout().addWidget(self.table)

    def refresh_data(self) -> None:
        """Load all songs from the backend."""
        self._all_songs = self.library_service.get_all_songs()
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply current filter to song list."""
        if self._current_filter is None:
            self._filtered_songs = self._all_songs
        else:
            filter_type, filter_id = self._current_filter
            if filter_type == 'album':
                self._filtered_songs = self.library_service.get_songs_by_album(filter_id)
            elif filter_type == 'artist':
                self._filtered_songs = self.library_service.get_songs_by_artist(filter_id)
            elif filter_type == 'genre':
                self._filtered_songs = self.library_service.get_songs_by_genre(filter_id)
            else:
                self._filtered_songs = self._all_songs

        self._populate_table()

    def _populate_table(self) -> None:
        """Populate table with filtered songs."""
        self.table.setRowCount(0)
        self.table.setRowCount(len(self._filtered_songs))

        for row, song in enumerate(self._filtered_songs):
            # Column 0: Track number
            track_item = QTableWidgetItem(str(song.track_number) if song.track_number else "")
            track_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            track_item.setFlags(track_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, track_item)

            # Column 1: Title
            title_item = QTableWidgetItem(song.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, title_item)

            # Column 2: Artist
            artist_item = QTableWidgetItem(song.artist)
            artist_item.setFlags(artist_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, artist_item)

            # Column 3: Album
            album_item = QTableWidgetItem(song.album)
            album_item.setFlags(album_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, album_item)

            # Column 4: Duration
            duration = int(song.duration) if song.duration else 0
            mins, secs = divmod(duration, 60)
            duration_str = f"{mins}:{secs:02d}"
            duration_item = QTableWidgetItem(duration_str)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, duration_item)

            # Column 5: Year
            year_item = QTableWidgetItem(str(song.year) if song.year else "")
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            year_item.setFlags(year_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, year_item)

    def filter_by_album(self, album_id: int) -> None:
        """Filter songs to show only those from the given album."""
        self._current_filter = ('album', album_id)
        self._apply_filter()

    def filter_by_artist(self, artist_id: int) -> None:
        """Filter songs to show only those from the given artist."""
        self._current_filter = ('artist', artist_id)
        self._apply_filter()

    def filter_by_genre(self, genre_id: int) -> None:
        """Filter songs to show only those from the given genre."""
        self._current_filter = ('genre', genre_id)
        self._apply_filter()

    def clear_filter(self) -> None:
        """Clear filter and show all songs."""
        self._current_filter = None
        self._apply_filter()

    @Slot()
    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click - play the song."""
        row = item.row()
        if 0 <= row < len(self._filtered_songs):
            song = self._filtered_songs[row]
            self.play_song_requested.emit(song)

    @Slot()
    def _show_context_menu(self, pos) -> None:
        """Show right-click context menu."""
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        if not (0 <= row < len(self._filtered_songs)):
            return

        song = self._filtered_songs[row]
        menu = QMenu(self)

        play_action = QAction("Play", self)
        play_action.triggered.connect(lambda: self.play_song_requested.emit(song))
        menu.addAction(play_action)

        menu.addSeparator()

        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self._add_to_queue(song))
        menu.addAction(add_queue_action)

        add_playlist_action = QAction("Add to Playlist...", self)
        add_playlist_action.triggered.connect(lambda: self._add_to_playlist(song))
        menu.addAction(add_playlist_action)

        menu.addSeparator()

        show_explorer_action = QAction("Show in Explorer", self)
        show_explorer_action.triggered.connect(lambda: self._show_in_explorer(song))
        menu.addAction(show_explorer_action)

        menu.exec(QCursor.pos())

    def _add_to_queue(self, song: Song) -> None:
        """Add song to playback queue."""
        if self.queue_service:
            self.queue_service.add_to_queue(song)

    def _add_to_playlist(self, song: Song) -> None:
        """Add song to a playlist - opens playlist selection dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QLabel, QMessageBox
        from src.backend.services.playlist import PlaylistServiceImpl
        
        playlist_service = PlaylistServiceImpl()
        playlists = playlist_service.get_all_playlists()
        
        if not playlists:
            QMessageBox.information(self, "No Playlists", "Create a playlist first from the Playlists view.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add to Playlist")
        dialog.resize(300, 400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(f"Add '{song.title}' to:"))
        
        list_widget = QListWidget()
        for pl in playlists:
            list_widget.addItem(f"{pl.name} ({pl.song_count} songs)")
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            current_row = list_widget.currentRow()
            if current_row >= 0:
                playlist_service.add_to_playlist(playlists[current_row].id, song)

    def _show_in_explorer(self, song: Song) -> None:
        """Open file location in Windows Explorer."""
        import subprocess
        import os
        if os.path.exists(song.path):
            # Properly quote path for explorer /select
            subprocess.run(["explorer", "/select,", os.path.normpath(song.path)], shell=True)

    def get_current_song(self) -> Optional[Song]:
        """Get the currently selected song."""
        row = self.table.currentRow()
        if 0 <= row < len(self._filtered_songs):
            return self._filtered_songs[row]
        return None

    def set_current_row(self, index: int) -> None:
        """Navigate to row by index."""
        if 0 <= index < len(self._filtered_songs):
            self.table.setCurrentCell(index, 1)

    def get_row_count(self) -> int:
        """Get the number of visible rows."""
        return self.table.rowCount()