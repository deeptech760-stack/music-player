"""Main application window for the music player."""
from __future__ import annotations
import os
import sys
from typing import Optional

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QHBoxLayout, QStatusBar, QWidget
from PySide6.QtCore import Qt, QCoreApplication, QFile, QTextStream, QTimer, QMetaObject, Q_ARG, Slot
from PySide6.QtGui import QPixmap

from src.frontend.components.sidebar import Sidebar
from src.frontend.components.now_playing_bar import NowPlayingBar
from src.frontend.components.particle_widget import ParticleWidget

from src.backend.services.interfaces import LibraryService, PlaybackService, QueueService, PlaylistService, SettingsService
from src.backend.models import Song, PlaybackState

# Import view widgets
from src.frontend.ui.songs_view import SongsView
from src.frontend.ui.albums_view import AlbumsView
from src.frontend.ui.artists_view import ArtistsView
from src.frontend.ui.genres_view import GenresView
from src.frontend.ui.queue_panel import QueuePanel
from src.frontend.ui.playlist_panel import PlaylistPanel
from src.frontend.ui.search_view import SearchView
from src.frontend.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Music player main window with sidebar, content area, and now-playing bar."""

    def __init__(
        self,
        library_service: LibraryService,
        playback_service: PlaybackService,
        queue_service: QueueService,
        playlist_service: PlaylistService,
        settings_service: SettingsService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        # Store service references
        self.library_service = library_service
        self.playback_service = playback_service
        self.queue_service = queue_service
        self.playlist_service = playlist_service
        self.settings_service = settings_service

        # Configure window
        QCoreApplication.setOrganizationName("MusicPlayer")
        QCoreApplication.setApplicationName("Music Player")
        self.setWindowTitle("Music Player")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Open maximized
        self.showMaximized()

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout for central widget
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create a container for sidebar + content area
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.item_clicked.connect(self._on_sidebar_item_clicked)
        content_layout.addWidget(self.sidebar, 0)  # Fixed width

        # Content area with particle background
        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        self.content_area.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        content_area_layout = QVBoxLayout(self.content_area)
        content_area_layout.setContentsMargins(0, 0, 0, 0)
        content_area_layout.setSpacing(0)

        # Content stack (on top of particles)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentStack")
        self.content_stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Setup views
        self._setup_views()

        content_area_layout.addWidget(self.content_stack, 1)
        
        # Now Playing Bar (always visible at bottom)
        self.now_playing_bar = NowPlayingBar(self)
        self.now_playing_bar.play_clicked.connect(self._on_play_clicked)
        self.now_playing_bar.pause_clicked.connect(self._on_pause_clicked)
        self.now_playing_bar.stop_clicked.connect(self._on_stop_clicked)
        self.now_playing_bar.prev_clicked.connect(self._on_prev_clicked)
        self.now_playing_bar.next_clicked.connect(self._on_next_clicked)
        self.now_playing_bar.seek_requested.connect(self._on_seek_requested)
        self.now_playing_bar.volume_changed.connect(self._on_volume_changed)

        content_area_layout.addWidget(self.now_playing_bar, 0)  # Fixed height

        content_layout.addWidget(self.content_area, 1)  # Expanding

        main_layout.addWidget(content_container, 1)

        # Load stylesheet
        self._load_stylesheet()

        # Register backend callbacks
        self._register_backend_callbacks()

        # Timer for periodic UI updates
        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._update_ui_from_playback)
        self._ui_timer.start(200)  # 5 FPS for position updates

    def _setup_views(self):
        """Create and add all views to the content stack."""
        # View 0: Library (Songs)
        self.library_view = SongsView(self.library_service, self.playback_service, self.queue_service)
        self.library_view.play_song_requested.connect(self._on_play_song_requested)
        self.content_stack.addWidget(self.library_view)

        # View 1: Albums
        self.albums_view = AlbumsView(self.library_service, self.playback_service, self.queue_service)
        self.albums_view.album_selected.connect(self._on_album_selected)
        self.content_stack.addWidget(self.albums_view)

        # View 2: Artists
        self.artists_view = ArtistsView(self.library_service, self.playback_service, self.queue_service)
        self.artists_view.artist_selected.connect(self._on_artist_selected)
        self.content_stack.addWidget(self.artists_view)

        # View 3: Genres
        self.genres_view = GenresView(self.library_service, self.playback_service, self.queue_service)
        self.genres_view.genre_selected.connect(self._on_genre_selected)
        self.content_stack.addWidget(self.genres_view)

        # View 4: Playlists
        self.playlist_panel = PlaylistPanel(self.library_service, self.playlist_service, self.queue_service)
        self.playlist_panel.play_song_requested.connect(self._on_play_song_requested)
        self.content_stack.addWidget(self.playlist_panel)

        # View 5: Queue
        self.queue_panel = QueuePanel(self.queue_service)
        self.queue_panel.play_song_requested.connect(self._on_play_song_requested)
        self.content_stack.addWidget(self.queue_panel)

        # View 6: Search
        self.search_view = SearchView(self.library_service)
        self.search_view.play_song_requested.connect(self._on_play_song_requested)
        self.content_stack.addWidget(self.search_view)

        # View 7: Settings (placeholder - opens dialog)
        from PySide6.QtWidgets import QLabel
        settings_widget = QWidget()
        settings_widget.setObjectName("SettingsWidget")
        settings_layout = QVBoxLayout(settings_widget)
        settings_label = QLabel("Settings\n(Click Settings in sidebar to open dialog)")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_label.setProperty("secondary", True)
        settings_layout.addWidget(settings_label)
        self.content_stack.addWidget(settings_widget)

    def _load_stylesheet(self):
        """Load QSS stylesheet from resources (works in dev and PyInstaller)."""
        # PyInstaller sets _MEIPASS to the temp extraction directory
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
        style_path = os.path.join(base_path, 'frontend', 'resources', 'style.qss')
        
        style_file = QFile(style_path)
        if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(style_file)
            self.setStyleSheet(stream.readAll())
            style_file.close()
        else:
            # Fallback: try relative path for development
            style_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'style.qss')
            style_file = QFile(style_path)
            if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                stream = QTextStream(style_file)
                self.setStyleSheet(stream.readAll())
                style_file.close()

    def _register_backend_callbacks(self):
        """Register callbacks with backend services."""
        # Playback position updates
        self.playback_service.on_position_changed(self._on_playback_position_changed)

        # Playback state changes
        self.playback_service.on_state_changed(self._on_playback_state_changed)

        # Track finished
        self.playback_service.on_track_finished(self._on_track_finished)

        # Queue changes
        self.queue_service.on_queue_changed(self._on_queue_changed)

    # --- Callback handlers (called from backend threads - use invokeMethod for thread safety) ---

    def _on_playback_position_changed(self, position: float):
        """Handle playback position update from backend."""
        QMetaObject.invokeMethod(
            self.now_playing_bar,
            "set_position",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(float, position),
        )

    def _on_playback_state_changed(self, state: PlaybackState):
        """Handle playback state change from backend."""
        QMetaObject.invokeMethod(
            self.now_playing_bar,
            "set_state",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, state.value),
        )

    def _on_track_finished(self):
        """Handle track finished from backend."""
        QMetaObject.invokeMethod(
            self,
            "_handle_track_finished",
            Qt.ConnectionType.QueuedConnection,
        )

    def _on_queue_changed(self):
        """Handle queue change from backend."""
        QMetaObject.invokeMethod(
            self,
            "_refresh_queue_view",
            Qt.ConnectionType.QueuedConnection,
        )

    # --- Slot methods (run in main thread) ---

    def _handle_track_finished(self):
        """Handle track finished - advance queue or repeat."""
        queue = self.queue_service.get_queue()
        current_idx = self.queue_service.get_current_index()

        repeat_mode = self.queue_service.get_repeat_mode()
        shuffle = self.queue_service.get_shuffle()

        if repeat_mode == 'one':
            # Replay current track
            if 0 <= current_idx < len(queue):
                self.playback_service.play(queue[current_idx].song)
        elif current_idx + 1 < len(queue):
            # Play next
            self.queue_service.set_current_index(current_idx + 1)
            next_song = queue[current_idx + 1].song
            self.playback_service.play(next_song)
        elif repeat_mode == 'all' and queue:
            # Loop to beginning
            self.queue_service.set_current_index(0)
            self.playback_service.play(queue[0].song)

    def _refresh_queue_view(self):
        """Refresh queue view when queue changes."""
        # Queue panel auto-refreshes via signal
        pass

    def _update_ui_from_playback(self):
        """Periodic UI update from playback service."""
        try:
            # Process queued events from background thread (position updates, track finished)
            self.playback_service.process_events()
            
            position = self.playback_service.get_position()
            duration = self.playback_service.get_duration()
            state = self.playback_service.get_state()

            if position >= 0:
                self.now_playing_bar.set_position(position)
                self.now_playing_bar.set_duration(duration)
            self.now_playing_bar.set_state(state.value)
        except Exception:
            pass  # Ignore errors during periodic update

    # --- Sidebar navigation ---

    def _on_sidebar_item_clicked(self, index: int):
        """Handle sidebar navigation."""
        # Special handling for Settings (index 7)
        if index == 7:
            self._show_settings_dialog()
        else:
            self.content_stack.setCurrentIndex(index)

    def _show_settings_dialog(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.settings_service, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    @Slot()
    def _on_settings_changed(self):
        """Handle settings changes."""
        # Refresh views that might need updated settings
        pass

    # --- Cross-view navigation handlers ---

    def _on_album_selected(self, album):
        """Handle album selection from AlbumsView - filter songs view."""
        self.library_view.filter_by_album(album.id)
        self.content_stack.setCurrentIndex(0)  # Switch to Songs view

    def _on_artist_selected(self, artist):
        """Handle artist selection from ArtistsView - filter songs view."""
        self.library_view.filter_by_artist(artist.id)
        self.content_stack.setCurrentIndex(0)  # Switch to Songs view

    def _on_genre_selected(self, genre):
        """Handle genre selection from GenresView - filter songs view."""
        self.library_view.filter_by_genre(genre.id)
        self.content_stack.setCurrentIndex(0)  # Switch to Songs view

    def _on_play_song_requested(self, song: Song):
        """Handle play request from SongsView, QueuePanel, PlaylistPanel, SearchView."""
        self.playback_service.play(song)
        self._update_now_playing_info(song)

    # --- Now Playing Bar action handlers ---

    def _on_play_clicked(self):
        """Handle play button click."""
        queue = self.queue_service.get_queue()
        current_idx = self.queue_service.get_current_index()

        if queue and 0 <= current_idx < len(queue):
            song = queue[current_idx].song
            self.playback_service.play(song)
            self._update_now_playing_info(song)

    def _on_pause_clicked(self):
        """Handle pause button click."""
        self.playback_service.pause()

    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.playback_service.stop()

    def _on_prev_clicked(self):
        """Handle previous button click."""
        queue = self.queue_service.get_queue()
        current_idx = self.queue_service.get_current_index()

        if queue and current_idx > 0:
            self.queue_service.set_current_index(current_idx - 1)
            song = queue[current_idx - 1].song
            self.playback_service.play(song)
            self._update_now_playing_info(song)

    def _on_next_clicked(self):
        """Handle next button click."""
        queue = self.queue_service.get_queue()
        current_idx = self.queue_service.get_current_index()

        if queue and current_idx + 1 < len(queue):
            self.queue_service.set_current_index(current_idx + 1)
            song = queue[current_idx + 1].song
            self.playback_service.play(song)
            self._update_now_playing_info(song)

    def _on_seek_requested(self, position: float):
        """Handle seek request from progress bar."""
        self.playback_service.seek(position)

    def _on_volume_changed(self, volume: float):
        """Handle volume change from slider."""
        self.playback_service.set_volume(volume)

    def _update_now_playing_info(self, song: Song):
        """Update now playing bar with song info."""
        self.now_playing_bar.set_track_info(
            title=song.title,
            artist=song.artist,
            album=song.album,
            artwork_path=song.artwork_path,
        )