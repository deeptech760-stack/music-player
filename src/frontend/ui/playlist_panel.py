"""Playlist panel for managing playlists."""
from __future__ import annotations
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QMenu,
    QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor, QColor, QAction

from src.backend.services.interfaces import PlaylistService, LibraryService
from src.backend.models import Playlist, Song


class PlaylistPanel(QWidget):
    """Playlist panel for managing playlists and their songs."""

    play_song_requested = Signal(Song)

    def __init__(
        self,
        library_service: LibraryService,
        playlist_service: PlaylistService,
        queue_service=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("PlaylistPanel")

        self.library_service = library_service
        self.playlist_service = playlist_service
        self.queue_service = queue_service

        self._playlists: List[Playlist] = []
        self._current_playlist_id: Optional[int] = None

        self._build_ui()
        self._connect_signals()
        self.refresh_playlists()

    def _build_ui(self) -> None:
        """Create the playlist panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 8, 8, 8)
        toolbar.setSpacing(8)

        self.new_btn = QPushButton("New Playlist")
        self.new_btn.setProperty("primary", True)
        self.new_btn.clicked.connect(self._create_playlist)
        toolbar.addWidget(self.new_btn)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setEnabled(False)
        self.rename_btn.clicked.connect(self._rename_playlist)
        toolbar.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_playlist)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()

        main_layout.addLayout(toolbar)

        # Splitter for playlists list and songs table
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # Left: Playlists list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(8, 0, 0, 8)

        self.playlist_list = QListWidget()
        self.playlist_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.playlist_list.setAlternatingRowColors(True)
        self.playlist_list.currentItemChanged.connect(self._on_playlist_selected)
        self.playlist_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self._show_playlist_context_menu)
        left_layout.addWidget(self.playlist_list)

        # Right: Songs in playlist
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 8, 8)

        self.songs_table = QTableWidget()
        self.songs_table.setColumnCount(4)
        self.songs_table.setHorizontalHeaderLabels(["#", "Title", "Artist", "Duration"])

        header = self.songs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.songs_table.setColumnWidth(0, 50)
        self.songs_table.setColumnWidth(3, 80)

        self.songs_table.verticalHeader().setVisible(False)
        self.songs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.songs_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.songs_table.setAlternatingRowColors(True)
        self.songs_table.setShowGrid(False)
        self.songs_table.setSortingEnabled(False)
        self.songs_table.itemDoubleClicked.connect(self._on_song_double_clicked)
        self.songs_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.songs_table.customContextMenuRequested.connect(self._show_song_context_menu)

        right_layout.addWidget(self.songs_table)

        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([300, 700])

        main_layout.addWidget(self.splitter, 1)

    def _connect_signals(self) -> None:
        """Connect signals."""
        pass

    def refresh_playlists(self) -> None:
        """Reload playlists from backend."""
        self._playlists = self.playlist_service.get_all_playlists()

        self.playlist_list.clear()
        for playlist in self._playlists:
            item = QListWidgetItem(playlist.name)
            item.setData(Qt.ItemDataRole.UserRole, playlist.id)
            item.setToolTip(f"{playlist.song_count} songs • {self._format_duration(playlist.total_duration)}")
            self.playlist_list.addItem(item)

        # Clear songs table
        self.songs_table.setRowCount(0)
        self._current_playlist_id = None
        self.rename_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _on_playlist_selected(self, current, previous) -> None:
        """Handle playlist selection."""
        if not current:
            self.songs_table.setRowCount(0)
            self._current_playlist_id = None
            self.rename_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        playlist_id = current.data(Qt.ItemDataRole.UserRole)
        self._current_playlist_id = playlist_id
        self.rename_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        self._load_playlist_songs(playlist_id)

    def _load_playlist_songs(self, playlist_id: int) -> None:
        """Load songs for the selected playlist."""
        songs = self.playlist_service.get_playlist_songs(playlist_id)

        self.songs_table.setRowCount(0)
        self.songs_table.setRowCount(len(songs))

        for row, song in enumerate(songs):
            # Column 0: Track number
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.songs_table.setItem(row, 0, num_item)

            # Column 1: Title
            title_item = QTableWidgetItem(song.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.songs_table.setItem(row, 1, title_item)

            # Column 2: Artist
            artist_item = QTableWidgetItem(song.artist)
            artist_item.setFlags(artist_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.songs_table.setItem(row, 2, artist_item)

            # Column 3: Duration
            duration = int(song.duration) if song.duration else 0
            mins, secs = divmod(duration, 60)
            duration_str = f"{mins}:{secs:02d}"
            duration_item = QTableWidgetItem(duration_str)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.songs_table.setItem(row, 3, duration_item)

    @Slot()
    def _create_playlist(self) -> None:
        """Create a new playlist."""
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist name:")
        if ok and name.strip():
            playlist = self.playlist_service.create_playlist(name.strip())
            self.refresh_playlists()
            # Select the new playlist
            for i in range(self.playlist_list.count()):
                item = self.playlist_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == playlist.id:
                    self.playlist_list.setCurrentItem(item)
                    break

    @Slot()
    def _rename_playlist(self) -> None:
        """Rename the selected playlist."""
        if not self._current_playlist_id:
            return

        current_item = self.playlist_list.currentItem()
        if not current_item:
            return

        old_name = current_item.text()
        name, ok = QInputDialog.getText(self, "Rename Playlist", "New name:", text=old_name)
        if ok and name.strip() and name.strip() != old_name:
            self.playlist_service.rename_playlist(self._current_playlist_id, name.strip())
            self.refresh_playlists()

    @Slot()
    def _delete_playlist(self) -> None:
        """Delete the selected playlist."""
        if not self._current_playlist_id:
            return

        current_item = self.playlist_list.currentItem()
        if not current_item:
            return

        reply = QMessageBox.question(
            self, "Delete Playlist",
            f"Delete playlist '{current_item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.playlist_service.delete_playlist(self._current_playlist_id)
            self.refresh_playlists()

    @Slot()
    def _on_song_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click on song - play it."""
        row = item.row()
        if not self._current_playlist_id:
            return

        songs = self.playlist_service.get_playlist_songs(self._current_playlist_id)
        if 0 <= row < len(songs):
            self.play_song_requested.emit(songs[row])

    @Slot()
    def _show_playlist_context_menu(self, pos) -> None:
        """Show context menu for playlist list."""
        item = self.playlist_list.itemAt(pos)
        if not item:
            return

        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        play_action = QAction("Play Playlist", self)
        play_action.triggered.connect(lambda: self._play_playlist(playlist_id))
        menu.addAction(play_action)

        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self._add_playlist_to_queue(playlist_id))
        menu.addAction(add_queue_action)

        menu.addSeparator()

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self._rename_playlist)
        menu.addAction(rename_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._delete_playlist)
        menu.addAction(delete_action)

        menu.exec(QCursor.pos())

    @Slot()
    def _show_song_context_menu(self, pos) -> None:
        """Show context menu for song table."""
        item = self.songs_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        if not self._current_playlist_id:
            return

        songs = self.playlist_service.get_playlist_songs(self._current_playlist_id)
        if not (0 <= row < len(songs)):
            return

        song = songs[row]
        menu = QMenu(self)

        play_action = QAction("Play", self)
        play_action.triggered.connect(lambda: self.play_song_requested.emit(song))
        menu.addAction(play_action)

        remove_action = QAction("Remove from Playlist", self)
        remove_action.triggered.connect(lambda: self._remove_from_playlist(song.id))
        menu.addAction(remove_action)

        menu.addSeparator()

        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self._add_to_queue(song))
        menu.addAction(add_queue_action)

        menu.exec(QCursor.pos())

    def _play_playlist(self, playlist_id: int) -> None:
        """Play all songs in the playlist."""
        songs = self.playlist_service.get_playlist_songs(playlist_id)
        if songs and self.queue_service:
            self.queue_service.clear_queue()
            for song in songs:
                self.queue_service.add_to_queue(song)
            self.queue_service.set_current_index(0)

    def _add_playlist_to_queue(self, playlist_id: int) -> None:
        """Add all playlist songs to queue."""
        songs = self.playlist_service.get_playlist_songs(playlist_id)
        if songs and self.queue_service:
            for song in songs:
                self.queue_service.add_to_queue(song)

    def _remove_from_playlist(self, song_id: int) -> None:
        """Remove song from current playlist."""
        if self._current_playlist_id:
            self.playlist_service.remove_from_playlist(self._current_playlist_id, song_id)
            self._load_playlist_songs(self._current_playlist_id)

    def _add_to_queue(self, song: Song) -> None:
        """Add song to playback queue."""
        if self.queue_service:
            self.queue_service.add_to_queue(song)

    def _format_duration(self, seconds: float) -> str:
        """Format duration as H:MM:SS or M:SS."""
        if seconds <= 0:
            return "0:00"
        secs = int(seconds)
        hours = secs // 3600
        mins = (secs % 3600) // 60
        secs = secs % 60
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"