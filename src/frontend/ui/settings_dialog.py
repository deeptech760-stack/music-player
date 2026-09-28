"""Settings dialog for the music player."""
from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QComboBox, QGroupBox, QLabel,
    QLineEdit, QCheckBox, QMessageBox, QFormLayout, QFileDialog,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from src.backend.services.interfaces import SettingsService
from src.backend.models import DEFAULT_SETTINGS


class SettingsDialog(QDialog):
    """Settings dialog for configuring the music player."""

    settings_changed = Signal()

    def __init__(
        self,
        settings_service: SettingsService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.settings_service = settings_service

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)

        self._build_ui()
        self._load_current_settings()

    def _build_ui(self) -> None:
        """Create the settings dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Create tabs
        self._create_library_tab()
        self._create_playback_tab()
        self._create_appearance_tab()
        self._create_advanced_tab()

        main_layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 12, 16, 16)
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setProperty("primary", True)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

    def _create_library_tab(self) -> None:
        """Create library settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Library paths
        paths_group = QGroupBox("Library Folders")
        paths_layout = QVBoxLayout(paths_group)

        self.paths_list = QListWidget()
        self.paths_list.setAlternatingRowColors(True)
        paths_layout.addWidget(self.paths_list)

        paths_buttons = QHBoxLayout()
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self._add_library_folder)
        paths_buttons.addWidget(self.add_folder_btn)

        self.remove_folder_btn = QPushButton("Remove")
        self.remove_folder_btn.clicked.connect(self._remove_library_folder)
        paths_buttons.addWidget(self.remove_folder_btn)
        paths_buttons.addStretch()

        paths_layout.addLayout(paths_buttons)
        layout.addWidget(paths_group)

        # Auto-scan
        self.auto_scan_checkbox = QCheckBox("Auto-scan library on startup")
        layout.addWidget(self.auto_scan_checkbox)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Library")

    def _create_playback_tab(self) -> None:
        """Create playback settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Default volume
        volume_group = QGroupBox("Default Volume")
        volume_layout = QVBoxLayout(volume_group)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("70%")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.volume_label)

        layout.addWidget(volume_group)

        # Crossfade (placeholder)
        crossfade_group = QGroupBox("Crossfade")
        crossfade_layout = QHBoxLayout(crossfade_group)

        crossfade_layout.addWidget(QLabel("Duration (ms):"))
        self.crossfade_input = QLineEdit("0")
        self.crossfade_input.setFixedWidth(80)
        self.crossfade_input.setPlaceholderText("0 = disabled")
        crossfade_layout.addWidget(self.crossfade_input)
        crossfade_layout.addStretch()

        layout.addWidget(crossfade_group)

        # Repeat/Shuffle defaults
        defaults_group = QGroupBox("Default Playback Mode")
        defaults_layout = QFormLayout(defaults_group)

        self.default_repeat_combo = QComboBox()
        self.default_repeat_combo.addItems(["Off", "One", "All"])
        defaults_layout.addRow("Repeat:", self.default_repeat_combo)

        self.default_shuffle_checkbox = QCheckBox("Shuffle by default")
        defaults_layout.addRow("", self.default_shuffle_checkbox)

        layout.addWidget(defaults_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Playback")

    def _create_appearance_tab(self) -> None:
        """Create appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Theme
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        theme_layout.addWidget(self.theme_combo)

        layout.addWidget(theme_group)

        # Accent color (placeholder)
        accent_group = QGroupBox("Accent Color")
        accent_layout = QVBoxLayout(accent_group)

        accent_layout.addWidget(QLabel("Primary accent color (requires restart):"))
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["Burgundy", "Blue", "Green", "Purple", "Orange"])
        accent_layout.addWidget(self.accent_combo)

        layout.addWidget(accent_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Appearance")

    def _create_advanced_tab(self) -> None:
        """Create advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Cache
        cache_group = QGroupBox("Cache")
        cache_layout = QFormLayout(cache_group)

        self.cache_size_input = QLineEdit("100")
        self.cache_size_input.setPlaceholderText("Max artwork cache (MB)")
        cache_layout.addRow("Artwork Cache Size:", self.cache_size_input)

        layout.addWidget(cache_group)

        # Database
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout(db_group)

        self.reset_db_btn = QPushButton("Reset Library Database")
        self.reset_db_btn.setStyleSheet("color: #ff6b6b;")
        self.reset_db_btn.clicked.connect(self._confirm_reset_database)
        db_layout.addWidget(self.reset_db_btn)

        db_layout.addWidget(QLabel("Warning: This will delete all library data and require a rescan."))
        layout.addWidget(db_group)

        # Diagnostics
        diag_group = QGroupBox("Diagnostics")
        diag_layout = QVBoxLayout(diag_group)

        self.show_logs_btn = QPushButton("Open Log File")
        self.show_logs_btn.clicked.connect(self._open_log_file)
        diag_layout.addWidget(self.show_logs_btn)

        layout.addWidget(diag_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced")

    @Slot()
    def _add_library_folder(self) -> None:
        """Add a library folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Music Folder", ""
        )
        if folder:
            self.paths_list.addItem(folder)

    @Slot()
    def _remove_library_folder(self) -> None:
        """Remove selected library folder."""
        current_row = self.paths_list.currentRow()
        if current_row >= 0:
            self.paths_list.takeItem(current_row)

    @Slot()
    def _confirm_reset_database(self) -> None:
        """Confirm and reset database."""
        reply = QMessageBox.question(
            self, "Reset Database",
            "This will delete ALL library data (songs, albums, artists, playlists, queue).\n"
            "You will need to rescan your music folders.\n\n"
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.settings_service.reset_to_defaults()
                QMessageBox.information(
                    self, "Database Reset",
                    "Database has been reset. Restart the application to rescan your library."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset database: {e}")

    @Slot()
    def _open_log_file(self) -> None:
        """Open log file location."""
        import os
        import subprocess
        log_path = os.path.join(os.environ.get("APPDATA", ""), "MusicPlayer", "music_player.log")
        if os.path.exists(log_path):
            subprocess.run(["notepad.exe", log_path])
        else:
            QMessageBox.information(self, "Log File", "Log file not found.")

    def _load_current_settings(self) -> None:
        """Load current settings from backend."""
        try:
            settings = self.settings_service.get_all()

            # Library
            library_paths = settings.get("library_paths", [])
            for path in library_paths:
                self.paths_list.addItem(path)

            self.auto_scan_checkbox.setChecked(settings.get("auto_scan_on_startup", True))

            # Playback
            self.volume_slider.setValue(int(settings.get("volume", 0.7) * 100))
            self.crossfade_input.setText(str(settings.get("crossfade_ms", 0)))
            repeat_mode = settings.get("repeat_mode", "off")
            self.default_repeat_combo.setCurrentText(repeat_mode.capitalize())
            self.default_shuffle_checkbox.setChecked(settings.get("shuffle", False))

            # Appearance
            theme = settings.get("theme", "dark")
            self.theme_combo.setCurrentText(theme.capitalize())

        except Exception:
            pass  # Use defaults

    @Slot()
    def _save_settings(self) -> None:
        """Save all settings to backend."""
        try:
            # Library
            paths = [self.paths_list.item(i).text() for i in range(self.paths_list.count())]
            self.settings_service.set("library_paths", paths)
            self.settings_service.set("auto_scan_on_startup", self.auto_scan_checkbox.isChecked())

            # Playback
            self.settings_service.set("volume", self.volume_slider.value() / 100.0)
            self.settings_service.set("crossfade_ms", int(self.crossfade_input.text() or 0))
            self.settings_service.set("repeat_mode", self.default_repeat_combo.currentText().lower())
            self.settings_service.set("shuffle", self.default_shuffle_checkbox.isChecked())

            # Appearance
            self.settings_service.set("theme", self.theme_combo.currentText().lower())
            self.settings_service.set("accent_color", self.accent_combo.currentText().lower())

            self.settings_changed.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")