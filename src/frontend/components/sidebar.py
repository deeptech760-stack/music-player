"""Sidebar navigation component."""
from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class Sidebar(QWidget):
    """Left sidebar navigation with app logo and menu items."""

    item_clicked = Signal(int)

    NAV_ITEMS = [
        ("♫  Library", "library"),
        ("📀  Albums", "albums"),
        ("👤  Artists", "artists"),
        ("🎵  Genres", "genres"),
        ("📋  Playlists", "playlists"),
        ("📋  Queue", "queue"),
        ("🔍  Search", "search"),
        ("⚙️  Settings", "settings"),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(200)
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # App logo/title
        self.logo_label = QLabel("♪ MusicPlayer")
        self.logo_label.setObjectName("SidebarLogo")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.logo_label.setStyleSheet("""
            QLabel {
                color: #c94f7c;
                padding: 20px 16px 16px 16px;
                background: transparent;
                border-bottom: 1px solid #2a1020;
            }
        """)
        layout.addWidget(self.logo_label)
        
        # Navigation list
        self.list = QListWidget()
        self.list.setObjectName("SidebarList")
        self.list.setFrameShape(self.list.Shape.NoFrame)
        self.list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        for text, key in self.NAV_ITEMS:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.list.addItem(item)
        
        self.list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list)
        
        self.setLayout(layout)
    
    def _on_row_changed(self, current_row: int):
        self.item_clicked.emit(current_row)
    
    def set_current_item(self, index: int):
        if 0 <= index < self.list.count():
            self.list.setCurrentRow(index)