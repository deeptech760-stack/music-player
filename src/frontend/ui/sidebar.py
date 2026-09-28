import sys
import os
from typing import Optional, List, Dict
from PySide6.QtWidgets import QFrame, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics, QIcon, QPen

from src.backend.models import Genre

class Sidebar(QFrame):
    """
    Fixed-width left sidebar with navigation.
    """

    item_clicked = Signal(int)
    artwork_updated = Signal(str)
    title_updated = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Component state
        self.current_index = 0
        self.library = []
        self.artwork = {}
        
        # Layout
        self.setFixedWidth(200)
        self.setStyleSheet("""
            background: #0d0d0f;
            border-right: 1px solid #2a1020;
            padding-right: 16px;
            width: 200px;
            min-height: 80px;
        """
        )

    def addItem(self, text: str, index: int, icon_name: str = ""):
        """
        Add item to sidebar.
        """
        item = QListWidgetItem()
        item.setText(text)
        item.setData(Qt.ItemDataRole.UserType + 1, index)
        
        item.setForeground(QColor("#a08090"))
        
        # Set icon
        if icon_name:
            item.setIcon(QIcon(icon_name))
        
        self.library.append((index, item))
        self.list_widget.addItem(item)

    def updateItem(self, index: int, new_text: str, new_icon: str):
        """
        Update item text and icon.
        """
        item = self.getItem(index)
        if item:
            item.setText(new_text)
            if new_icon:
                item.setIcon(QIcon(new_icon))

    def getItem(self, index: int) -> Optional[QListWidgetItem]:
        """
        Get item from library.
        """
        for _, item in self.library:
            if item.data(Qt.ItemDataRole.UserType + 1) == index:
                return item
        return None

    @Slot(int)
    def setCurrentIndex(self, index: int):
        """
        Set current index to selected item.
        """
        if index < 0 or index >= len(self.library):
            return
        
        self.current_index = index
        self.update_selected_item()

    def update_selected_item(self):
        """
        Update item state.
        """
        count = self.list_widget.count()
        if count == 0:
            return
        
        # Find selected item
        selected_idx = -1
        for i in range(count):
            if self.library[i][0] == self.current_index:
                selected_idx = i
                break
        
        if selected_idx < 0:
            return
        
        item = self.library[selected_idx][1]
        if not item:
            return
        
        # Remove previous selection
        prev_idx = self.list_widget.currentRow()
        if prev_idx != -1:
            prev_item = self.library[prev_idx][1]
            if prev_item:
                prev_item.setSelected(False)
        
        # Add new selection
        item.setSelected(True)
        self.list_widget.setCurrentRow(selected_idx)

    def paintEvent(self, event):
        """
        Draw sidebar background and ensure title is visible.
        """
        if not self.isVisible():
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        bg_color = QColor("#0f0f11")
        painter.fillRect(self.rect(), bg_color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Recalculate layout
        list_height = self.rect().height() - 40
        self.list_widget.setMinimumHeight(list_height)
        
        # Update current item if list exists
        if hasattr(self, 'list_widget') and self.list_widget:
            self._update_selected_item()