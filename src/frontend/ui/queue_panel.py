"""Queue panel for managing playback queue."""
from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QVBoxLayout, QWidget, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot, QMetaObject, Q_ARG, QTimer
from PySide6.QtGui import QCursor, QColor, QAction

from src.backend.services.interfaces import QueueService
from src.backend.models import QueueItem


class QueuePanel(QWidget):
    """Queue panel displaying and managing the playback queue."""

    play_song_requested = Signal(QueueItem)

    def __init__(
        self,
        queue_service: QueueService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("QueuePanel")
        self.queue_service = queue_service

        self._build_ui()
        self._connect_signals()

        # Initial load
        QTimer.singleShot(0, self.refresh)

    def _build_ui(self) -> None:
        """Create the queue panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        # Table
        self.table = QTableWidget()
        self.table.setObjectName("QueueTable")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Title", "Artist", "Duration"])

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(3, 80)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(False)

        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        """Connect backend signals."""
        self.queue_service.on_queue_changed(self._on_queue_changed)

    @Slot()
    def _on_queue_changed(self) -> None:
        """Handle queue change from backend."""
        QMetaObject.invokeMethod(
            self, "refresh", Qt.ConnectionType.QueuedConnection
        )

    def refresh(self) -> None:
        """Refresh queue from backend."""
        if not self.queue_service:
            return

        queue = self.queue_service.get_queue()
        current_idx = self.queue_service.get_current_index()

        self.table.setRowCount(0)
        self.table.setRowCount(len(queue))

        for row, item in enumerate(queue):
            song = item.song

            # Column 0: Queue number
            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, num_item)

            # Column 1: Title
            title_item = QTableWidgetItem(song.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, title_item)

            # Column 2: Artist
            artist_item = QTableWidgetItem(song.artist)
            artist_item.setFlags(artist_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, artist_item)

            # Column 3: Duration
            duration = int(song.duration) if song.duration else 0
            mins, secs = divmod(duration, 60)
            duration_str = f"{mins}:{secs:02d}"
            duration_item = QTableWidgetItem(duration_str)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, duration_item)

        # Highlight current playing
        if 0 <= current_idx < len(queue):
            self._highlight_row(current_idx)

    def _highlight_row(self, row: int) -> None:
        """Highlight the currently playing row."""
        highlight_color = QColor("#c94f7c")
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(highlight_color)

    @Slot()
    def _show_context_menu(self, pos) -> None:
        """Show right-click context menu."""
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        queue = self.queue_service.get_queue()
        if not (0 <= row < len(queue)):
            return

        menu = QMenu(self)

        remove_action = QAction("Remove from Queue", self)
        remove_action.triggered.connect(lambda: self.queue_service.remove_from_queue(row))
        menu.addAction(remove_action)

        move_top_action = QAction("Move to Top", self)
        move_top_action.triggered.connect(lambda: self.queue_service.move_in_queue(row, 0))
        menu.addAction(move_top_action)

        menu.addSeparator()

        clear_action = QAction("Clear Queue", self)
        clear_action.triggered.connect(self.queue_service.clear_queue)
        menu.addAction(clear_action)

        menu.exec(QCursor.pos())