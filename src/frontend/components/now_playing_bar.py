from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QSlider, QGridLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QSpacerItem
from PySide6.QtGui import QColor, QPalette, QFont, QPixmap, Qt
from PySide6.QtCore import Signal, Slot, QObject, QTimer, Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup


class NowPlayingBar(QWidget):
    """
    A collapsible now playing bar with two states: collapsed (compact) and expanded (full controls).
    """

    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    prev_clicked = Signal()
    next_clicked = Signal()
    seek_requested = Signal(float)
    volume_changed = Signal(float)
    state_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NowPlayingBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # State
        self._slider_pressed = False
        self._total_duration = 0.0
        self._repeat_mode = "off"
        self._shuffle_enabled = False
        self._is_expanded = False
        
        # Animation
        self._animation = None
        
        # Build
        self.setPalette(self._create_dark_palette())
        self.setFont(QFont("Segoe UI", 10))
        
        # Initialize attributes
        self._slider_pressed = False
        self._total_duration = 0.0
        self._repeat_mode = "off"
        self._shuffle_enabled = False
        self._is_expanded = False
        
        # Build UI
        self._build_ui()
        self._setup_connections()
        
        # Start in collapsed state - visible at bottom
        self._collapse(animate=False)

    def _create_dark_palette(self):
        """Define the dark burgundy glassmorphism theme palette."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#23121a"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#f4dcdc"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#2d1528"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f4dcdc"))
        palette.setColor(QPalette.ColorRole.Light, QColor("#3b1f3b"))
        palette.setColor(QPalette.ColorRole.Midlight, QColor("#4f2b53"))
        palette.setColor(QPalette.ColorRole.Dark, QColor("#1a0611"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#9a5077"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#f4dcdc"))
        # Set disabled button text color
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#5a2b4a"))
        # ToolTip is not a valid ColorRole - use ToolTipBase and ToolTipText instead
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#23121a"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f4dcdc"))
        # ActiveCaption and InactiveCaption are not valid ColorRole enums
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#be385f"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#f4dcdc"))
        return palette

    def _build_ui(self):
        """Build the entire UI layout with all widgets."""
        self._slider_pressed = False
        self._total_duration = 0.0
        self._repeat_mode = "off"
        self._shuffle_enabled = False
        self._is_expanded = False

        # === MAIN LAYOUT (single, created once) ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === COLLAPSED BAR (always visible) ===
        self.compact_bar = QWidget()
        self.compact_bar.setObjectName("CompactBar")
        self.compact_bar.setFixedHeight(60)  # Fixed height for collapsed state

        # Single layout for compact_bar - created ONCE
        compact_layout = QHBoxLayout(self.compact_bar)
        compact_layout.setContentsMargins(16, 8, 16, 8)
        compact_layout.setSpacing(12)

        # LEFT: Artwork (small)
        self.artwork_label = QLabel()
        self.artwork_label.setFixedSize(40, 40)
        self.artwork_label.setScaledContents(True)
        self._set_placeholder_artwork()
        self._apply_artwork_style()

        # CENTER: Track info + progress (compact)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)

        self.title_label = QLabel("No track playing")
        self.title_label.setStyleSheet("font-family: Segoe UI; font-size: 11px; font-weight: 600; color: #f4dcdc;")
        self.title_label.setWordWrap(True)

        self.artist_album_label = QLabel()
        self.artist_album_label.setStyleSheet("font-family: Segoe UI; font-size: 9px; color: #764d68;")
        self.artist_album_label.setAlignment(Qt.AlignLeft)

        # Compact progress row
        progress_row = QHBoxLayout()
        progress_row.setSpacing(6)
        progress_row.setContentsMargins(0, 0, 0, 0)

        self.current_time_label = QLabel("0:00")
        self.current_time_label.setStyleSheet("font-family: Segoe UI Mono; font-size: 9px; color: #ffffff;")
        self.current_time_label.setFixedWidth(35)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setFixedHeight(4)
        self.progress_slider.setCursor(Qt.PointingHandCursor)

        self.total_time_label = QLabel("0:00")
        self.total_time_label.setStyleSheet("font-family: Segoe UI Mono; font-size: 9px; color: #ffffff;")
        self.total_time_label.setFixedWidth(35)

        progress_row.addWidget(self.current_time_label)
        progress_row.addWidget(self.progress_slider, 1)
        progress_row.addWidget(self.total_time_label)

        center_layout.addWidget(self.title_label)
        center_layout.addWidget(self.artist_album_label)
        center_layout.addLayout(progress_row)

        center_widget.setLayout(center_layout)

        # RIGHT: Compact controls
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.addStretch()

        # Compact controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)

        self.shuffle_btn = self._make_compact_control_button("⇄", "Shuffle", checkable=True)
        self.prev_btn = self._make_compact_control_button("⏮", "Previous")
        self.play_btn = self._make_compact_control_button("▶", "Play", primary=True)
        self.next_btn = self._make_compact_control_button("⏭", "Next")
        self.repeat_btn = self._make_compact_control_button("🔁", "Repeat", checkable=True)

        controls_layout.addWidget(self.shuffle_btn)
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addWidget(self.repeat_btn)

        right_layout.addLayout(controls_layout)
        right_layout.addSpacing(8)

        # Volume
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(4)

        self.volume_btn = self._make_volume_button("🔊", "Mute")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setCursor(Qt.PointingHandCursor)
        self.volume_slider.setFixedHeight(4)

        volume_layout.addWidget(self.volume_btn)
        volume_layout.addWidget(self.volume_slider)

        right_layout.addLayout(volume_layout)

        # Expand/collapse toggle
        self.expand_btn = QPushButton("▲")
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setToolTip("Expand Now Playing")
        self.expand_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #9a5077;
                font-size: 12px;
                font-family: Segoe UI Emoji;
                border-radius: 4px;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(205, 79, 124, 0.15);
                border-radius: 4px;
            }
        """)
        self.expand_btn.clicked.connect(self._toggle_expand)
        right_layout.addWidget(self.expand_btn)

        right_layout.addStretch()

        # Add widgets to compact layout (single layout)
        compact_layout.addWidget(self.artwork_label, 0, Qt.AlignVCenter)
        compact_layout.addWidget(center_widget, 1)
        compact_layout.addWidget(right_widget)

        # === EXPANDED SECTION (initially hidden) ===
        self.expanded_widget = QWidget()
        self.expanded_widget.setObjectName("ExpandedWidget")
        self.expanded_widget.hide()

        # Single layout for expanded_widget - created ONCE
        expanded_main_layout = QVBoxLayout(self.expanded_widget)
        expanded_main_layout.setContentsMargins(24, 24, 24, 24)
        expanded_main_layout.setSpacing(18)
        # Don't set alignment on main layout - let widgets control their own alignment

        # 1. Artwork (larger, centered)
        self.expanded_artwork = QLabel()
        self.expanded_artwork.setFixedSize(120, 120)
        self.expanded_artwork.setAlignment(Qt.AlignCenter)
        self.expanded_artwork.setScaledContents(True)
        self.expanded_artwork.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._set_expanded_placeholder_artwork()
        self._apply_expanded_artwork_style()

        # 2. Track info (centered under artwork)
        self.expanded_title = QLabel("No track playing")
        self.expanded_title.setStyleSheet("font-family: Segoe UI; font-size: 18px; font-weight: 600; color: #f4dcdc;")
        self.expanded_title.setAlignment(Qt.AlignCenter)
        self.expanded_title.setWordWrap(True)
        self.expanded_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.expanded_artist = QLabel()
        self.expanded_artist.setStyleSheet("font-family: Segoe UI; font-size: 13px; color: #a08090;")
        self.expanded_artist.setAlignment(Qt.AlignCenter)
        self.expanded_artist.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.expanded_album = QLabel()
        self.expanded_album.setStyleSheet("font-family: Segoe UI; font-size: 11px; color: #764d68;")
        self.expanded_album.setAlignment(Qt.AlignCenter)
        self.expanded_album.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 3. Progress bar with time labels
        self.expanded_progress = QSlider(Qt.Horizontal)
        self.expanded_progress.setRange(0, 1000)
        self.expanded_progress.setValue(0)
        self.expanded_progress.setCursor(Qt.PointingHandCursor)
        self.expanded_progress.setFixedHeight(8)
        self.expanded_progress.setFixedWidth(400)
        self.expanded_progress.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.expanded_current_time = QLabel("0:00")
        self.expanded_current_time.setStyleSheet("font-family: Segoe UI Mono; font-size: 11px; color: #ffffff;")
        self.expanded_current_time.setFixedWidth(45)

        self.expanded_total_time = QLabel("0:00")
        self.expanded_total_time.setStyleSheet("font-family: Segoe UI Mono; font-size: 11px; color: #ffffff;")
        self.expanded_total_time.setFixedWidth(45)

        exp_progress_row = QHBoxLayout()
        exp_progress_row.setSpacing(10)
        exp_progress_row.setContentsMargins(0, 0, 0, 0)
        exp_progress_row.addStretch()
        exp_progress_row.addWidget(self.expanded_current_time)
        exp_progress_row.addWidget(self.expanded_progress, 1)
        exp_progress_row.addWidget(self.expanded_total_time)
        exp_progress_row.addStretch()

        # 4. Main playback controls (centered row: Previous | Play/Pause | Next)
        self.exp_prev_btn = self._make_expanded_control_button("⏮", "Previous")
        self.exp_play_btn = self._make_expanded_control_button("▶", "Play", primary=True)
        self.exp_next_btn = self._make_expanded_control_button("⏭", "Next")

        # Make play button larger
        self.exp_play_btn.setFixedSize(56, 56)
        self.exp_play_btn.setStyleSheet(self.exp_play_btn.styleSheet().replace("font-size: 22px", "font-size: 28px"))
        self.exp_prev_btn.setFixedSize(44, 44)
        self.exp_next_btn.setFixedSize(44, 44)

        exp_controls_layout = QHBoxLayout()
        exp_controls_layout.setSpacing(24)
        exp_controls_layout.setContentsMargins(0, 0, 0, 0)
        exp_controls_layout.addStretch()
        exp_controls_layout.addWidget(self.exp_prev_btn)
        exp_controls_layout.addWidget(self.exp_play_btn)
        exp_controls_layout.addWidget(self.exp_next_btn)
        exp_controls_layout.addStretch()

        # Collapse button
        self.collapse_btn = QPushButton("▼")
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setToolTip("Collapse Now Playing")
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: rgba(205, 79, 124, 0.15);
                color: #c94f7c;
                font-size: 14px;
                font-family: Segoe UI Emoji;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: rgba(205, 79, 124, 0.3);
            }
        """)
        self.collapse_btn.clicked.connect(self._toggle_expand)

        # Assemble expanded layout - clean vertical flow with fixed spacing
        expanded_main_layout.addStretch(1)
        expanded_main_layout.addWidget(self.expanded_artwork, 0, Qt.AlignHCenter)
        expanded_main_layout.addSpacing(12)
        expanded_main_layout.addWidget(self.expanded_title, 0, Qt.AlignHCenter)
        expanded_main_layout.addSpacing(4)
        expanded_main_layout.addWidget(self.expanded_artist, 0, Qt.AlignHCenter)
        expanded_main_layout.addSpacing(4)
        expanded_main_layout.addWidget(self.expanded_album, 0, Qt.AlignHCenter)
        expanded_main_layout.addSpacing(16)
        expanded_main_layout.addLayout(exp_progress_row)
        expanded_main_layout.addSpacing(16)
        expanded_main_layout.addLayout(exp_controls_layout)
        expanded_main_layout.addSpacing(20)
        expanded_main_layout.addWidget(self.collapse_btn, 0, Qt.AlignHCenter)
        expanded_main_layout.addStretch(1)

        # Constrain expanded widget width for centered alignment
        self.expanded_widget.setMaximumWidth(500)
        self.expanded_widget.setMinimumHeight(320)

        # Add compact and expanded to main layout (single main_layout)
        self.main_layout.addWidget(self.compact_bar)
        self.main_layout.addWidget(self.expanded_widget, alignment=Qt.AlignHCenter)

        # Initial collapsed state - visible at 60px
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)

    def _create_dark_palette(self):
        """Define the dark burgundy glassmorphism theme palette."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#23121a"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#f4dcdc"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#2d1528"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f4dcdc"))
        palette.setColor(QPalette.ColorRole.Light, QColor("#3b1f3b"))
        palette.setColor(QPalette.ColorRole.Midlight, QColor("#4f2b53"))
        palette.setColor(QPalette.ColorRole.Dark, QColor("#1a0611"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#9a5077"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#f4dcdc"))
        # Set disabled button text color
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#5a2b4a"))
        # ToolTip is not a valid ColorRole - use ToolTipBase and ToolTipText instead
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#23121a"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f4dcdc"))
        # ActiveCaption and InactiveCaption are not valid ColorRole enums
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#be385f"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#f4dcdc"))
        return palette

    def _apply_artwork_style(self):
        """Apply style to compact artwork."""
        self.artwork_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #4a0d2a, stop:1 #1a0d14);
                border-radius: 6px;
                border: 1px solid rgba(228, 105, 188, 0.3);
                color: #c94f7c;
            }
        """)

    def _apply_expanded_artwork_style(self):
        self.expanded_artwork.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #4a0d2a, stop:1 #1a0d14);
                border-radius: 12px;
                border: 1px solid rgba(228, 105, 188, 0.3);
                color: #c94f7c;
            }
        """)

    def _make_compact_control_button(self, glyph, tooltip, primary=False, checkable=False):
        """Create a compact control button."""
        btn = QPushButton(glyph)
        btn.setMinimumSize(28, 28)
        btn.setMaximumSize(28, 28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(checkable)

        default_style = "border: none; background: transparent; font-size: 14px; font-family: 'Segoe UI Symbol', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif; padding: 0; margin: 0; border-radius: 4px; box-shadow: none"
        hover_style = "border-radius: 4px; background: rgba(205, 79, 124, 0.16); box-shadow: 0 1px 3px rgba(205, 79, 124, 0.16)"

        if primary:
            btn.setStyleSheet(f"{default_style}; color: #f4dcdc; {hover_style}")
        else:
            btn.setStyleSheet(f"{default_style}; color: #9a5077; {hover_style}")

        btn.setToolTip(tooltip)
        return btn

    def _make_expanded_control_button(self, glyph, tooltip, primary=False, checkable=False):
        btn = QPushButton(glyph)
        btn.setMinimumSize(44, 44)
        btn.setMaximumSize(44, 44)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setCheckable(checkable)

        default_style = "border: none; background: transparent; font-size: 22px; font-family: 'Segoe UI Symbol', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif; padding: 2px; margin: 0; border-radius: 6px; box-shadow: none"
        hover_style = "border-radius: 8px; background: rgba(205, 79, 124, 0.16); box-shadow: 0 2px 5px rgba(205, 79, 124, 0.16)"

        if primary:
            btn.setStyleSheet(f"{default_style}; color: #f4dcdc; {hover_style}")
        else:
            btn.setStyleSheet(f"{default_style}; color: #9a5077; {hover_style}")

        btn.setToolTip(tooltip)
        return btn

    def _make_volume_button(self, glyph, tooltip):
        btn = QPushButton(glyph)
        btn.setMinimumSize(24, 24)
        btn.setMaximumSize(24, 24)
        btn.setCursor(Qt.PointingHandCursor)

        mute_style = "border: none; background: transparent; color: #9a5077; font-size: 14px; font-family: 'Segoe UI Symbol', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif; padding: 0; margin: 0"
        hover_style = "border-radius: 4px; background: rgba(205, 79, 124, 0.16)"
        btn.setStyleSheet(mute_style)

        btn.setToolTip(tooltip)
        return btn

    def _setup_connections(self):
        """Bind widget signals to internal callbacks."""
        # Compact bar connections
        self.play_btn.clicked.connect(self._on_play_click)
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        self.shuffle_btn.toggled.connect(lambda checked: self._on_shuffle_toggled(checked))
        self.repeat_btn.toggled.connect(lambda checked: self._on_repeat_toggled(checked))

        self.exp_play_btn.clicked.connect(self._on_play_click)
        self.exp_prev_btn.clicked.connect(self.prev_clicked.emit)
        self.exp_next_btn.clicked.connect(self.next_clicked.emit)

        # Progress sliders
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)

        self.expanded_progress.sliderPressed.connect(self._on_slider_pressed)
        self.expanded_progress.sliderReleased.connect(self._on_slider_released)
        self.expanded_progress.sliderMoved.connect(self._on_slider_moved)

        # Volume slider (compact only)
        self.volume_slider.valueChanged.connect(self._on_volume_changed_compact)

        self._slider_pressed = False

    def _toggle_expand(self):
        """Toggle between collapsed and expanded state."""
        if self._is_expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self, animate=True):
        """Expand the Now Playing bar."""
        if self._is_expanded:
            return
        
        self._is_expanded = True
        self.expand_btn.setText("▼")
        self.expand_btn.setToolTip("Collapse Now Playing")
        
        self.expanded_widget.show()
        self.collapse_btn.show()
        
        if animate:
            self._animate_height(320, True)
        else:
            self.setMinimumHeight(320)
            self.setMaximumHeight(320)
        
        self._is_expanded = True
        self._sync_expanded_state()

    def _collapse(self, animate=True):
        """Collapse the Now Playing bar."""
        if not self._is_expanded:
            return
        
        self._is_expanded = False
        self.expand_btn.setText("▲")
        self.expand_btn.setToolTip("Expand Now Playing")
        
        self.expanded_widget.hide()
        self.collapse_btn.hide()
        
        if animate:
            self._animate_height(60, False)
        else:
            self.setMinimumHeight(60)
            self.setMaximumHeight(60)
        
        self._is_expanded = False

    def _animate_height(self, target_height, expanding):
        """Animate height change."""
        if self._animation:
            self._animation.stop()
        
        self._animation = QPropertyAnimation(self, b"maximumHeight")
        self._animation.setDuration(250)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.setStartValue(self.height())
        self._animation.setEndValue(target_height)
        self._animation.finished.connect(lambda: self.setMaximumHeight(target_height))
        self._animation.start()

    def _sync_expanded_state(self):
        """Sync expanded controls with current state."""
        self.exp_play_btn.setText(self.play_btn.text())

    def _on_play_click(self):
        """Toggle play/pause state."""
        glyph = self.play_btn.text()

        if glyph == "⏸":
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()

        self._set_play_state("⏸" if glyph != "⏸" else "▶")

    def _set_play_state(self, glyph):
        self.play_btn.setText(glyph)
        self.exp_play_btn.setText(glyph)

    def _on_shuffle_toggled(self, checked):
        self.shuffle_btn.setChecked(checked)
        self.exp_shuffle_btn.setChecked(checked)
        self._shuffle_enabled = checked

    def _on_repeat_toggled(self, checked):
        self.repeat_btn.setChecked(checked)
        self.exp_repeat_btn.setChecked(checked)
        self._repeat_mode = "one" if checked else "off"
        self._update_repeat_icons()

    def _update_repeat_icons(self):
        if self._repeat_mode == "one":
            self.repeat_btn.setText("🔂")
            self.exp_repeat_btn.setText("🔂")
        elif self._repeat_mode == "all":
            self.repeat_btn.setText("🔁")
            self.exp_repeat_btn.setText("🔁")
        else:
            self.repeat_btn.setText("🔁")
            self.exp_repeat_btn.setText("🔁")

    def set_track_info(self, title, artist, album, artwork_path):
        """
        Set metadata, artwork, and time labels.
        """
        self.title_label.setText(title)
        self.expanded_title.setText(title)

        album_info = []

        if artist and album:
            album_info = [artist, "·", album]
        elif artist:
            album_info = [artist]
        elif album:
            album_info = [album]

        self.artist_album_label.setText("")

        if album_info:
            self.artist_album_label.setText(" ".join(album_info))
        
        self.expanded_artist.setText(artist)
        self.expanded_album.setText(album)
        self.expanded_title.setText(title)

        if artwork_path:
            self._load_artwork(artwork_path)
            self._load_expanded_artwork(artwork_path)
        else:
            self._set_placeholder_artwork()
            self._set_expanded_placeholder_artwork()

    def _load_artwork(self, path):
        """Try to load artwork from file or fall back to gradient."""
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.artwork_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.expanded_artwork.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        except Exception:
            pass

        self._set_placeholder_artwork()
        self._set_expanded_placeholder_artwork()

    def _load_expanded_artwork(self, path):
        """Load expanded artwork."""
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.expanded_artwork.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        except Exception:
            pass
        self._set_expanded_placeholder_artwork()

    def _set_placeholder_artwork(self):
        """Create a music-note gradient placeholder for compact."""
        self.artwork_label.setText("♪")
        self._apply_artwork_style()

    def _set_expanded_placeholder_artwork(self):
        """Create a music-note gradient placeholder for expanded."""
        self.expanded_artwork.setText("♪")
        self.expanded_artwork.setAlignment(Qt.AlignCenter)
        self.expanded_artwork.setFont(QFont("Segoe UI", 48))
        self.expanded_artwork.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #4a0d2a, stop:1 #1a0d14);
                border-radius: 16px;
                border: 1px solid rgba(228, 105, 188, 0.3);
                color: #c94f7c;
            }
        """)

    def _apply_artwork_style(self):
        self.artwork_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #4a0d2a, stop:1 #1a0d14);
                border-radius: 6px;
                border: 1px solid rgba(228, 105, 188, 0.3);
                color: #c94f7c;
            }
        """)

    def _format_time(self, seconds):
        """
        Convert seconds to M:SS or H:MM:SS.
        """
        if seconds <= 0:
            return "0:00"

        seconds = int(seconds)

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"

        return f"{minutes}:{secs:02d}"

    def set_position(self, position):
        """
        Update playback position on the slider and time labels.
        """
        if not self._slider_pressed:
            # Calculate slider value based on duration
            max_val = int(self._total_duration * 100)
            if max_val > 0:
                percentage = max(0, min(1000, int(position * max_val)))
                self.progress_slider.setValue(percentage)
                self.expanded_progress.setValue(percentage)

            current_seconds = position * self._total_duration
            self.current_time_label.setText(self._format_time(current_seconds))
            self.expanded_current_time.setText(self._format_time(current_seconds))

    def set_duration(self, duration):
        """
        Set total track duration.
        """
        self._total_duration = duration
        total_str = self._format_time(duration)
        self.total_time_label.setText(total_str)
        self.expanded_total_time.setText(total_str)

    def set_play_state(self, state):
        """
        Set the active playback state.
        """
        if state == "playing":
            self.play_btn.setText("⏸")
            self.exp_play_btn.setText("⏸")
        elif state == "paused":
            self.play_btn.setText("▶")
            self.exp_play_btn.setText("▶")
        elif state == "stopped":
            self.play_btn.setText("▶")
            self.exp_play_btn.setText("▶")

    def set_repeat_mode(self, mode):
        """
        Set repeat icon mode.
        """
        self._repeat_mode = mode
        if mode == "one":
            self.repeat_btn.setText("🔂")
            self.exp_repeat_btn.setText("🔂")
        elif mode == "all":
            self.repeat_btn.setText("🔁")
            self.exp_repeat_btn.setText("🔁")
        else:
            self.repeat_btn.setText("🔁")
            self.exp_repeat_btn.setText("🔁")

    def set_shuffle(self, enabled):
        """
        Set shuffle mode.
        """
        self._shuffle_enabled = enabled
        self.shuffle_btn.setChecked(enabled)
        self.exp_shuffle_btn.setChecked(enabled)

    def set_volume(self, value):
        """
        Set slider value and update mute button text.
        """
        self.volume_slider.setValue(int(value * 100))

        if value == 0:
            self.volume_btn.setText("🔇")
        elif value < 0.5:
            self.volume_btn.setText("🔈")
        else:
            self.volume_btn.setText("🔊")

    def _on_volume_changed_compact(self, value):
        """
        Handle volume slider motion from compact bar.
        """
        mute = value == 0
        if mute:
            self.volume_btn.setText("🔇")
        elif value < 50:
            self.volume_btn.setText("🔈")
        else:
            self.volume_btn.setText("🔊")
        self.volume_changed.emit(value / 100.0)

    def _on_slider_pressed(self):
        self._slider_pressed = True

    def _on_slider_released(self):
        self._slider_pressed = False
        position = self.progress_slider.value() / 1000.0
        self.seek_requested.emit(position)

    def _on_slider_moved(self, value):
        if self._slider_pressed:
            self.current_time_label.setText(self._format_time(value / 1000.0 * self._total_duration))
            self.expanded_current_time.setText(self._format_time(value / 1000.0 * self._total_duration))

    def __del__(self):
        pass