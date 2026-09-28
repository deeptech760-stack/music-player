from PySide6.QtWidgets import QLabel, QSpacerItem, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush
from PySide6.QtCore import Qt

import sys

class ArtworkLabel(QLabel):
    """
    A rounded rectangular label with a placeholder image.
    The image is rendered in the theme accent color.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure Widget
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            background-color: transparent;
            border: 1px solid #4a1d3a;
            border-radius: 8px;
            margin: 8px;
            aspect-ratio: 1 / 1;
        """)
        
        # Force placeholder rendering
        self.setPixmap(self.generate_placeholder())
        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Maintain aspect ratio
        side = min(self.width(), self.height())
        self.setFixedSize(side, side)

    def generate_placeholder(self):
        """
        Create a circular placeholder with a gradient accent color.
        """
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        
        # Calculate a centered circle
        rect = self.rect() 
        radius = min(rect.width(), rect.height()) // 2
        center = rect.center()
        
        # Create gradient fill
        brush = QBrush(QColor(139, 26, 58))  # Deep Burgundy
        brush.setStyle(QBrush.Style.SolidPattern) # 1
        
        # Draw the shape
        painter.setBrush(brush)
        painter.drawEllipse(center.x()-radius, center.y()-radius, radius*2, radius*2)
        
        painter.end()
        
        return pixmap

    def paintEvent(self, event):
        """
        Handle custom painting to ensure the placeholder stays centered.
        """
        super().paintEvent(event)

    def setPixmap(self, pixmap):
        """
        Set pixmap and preserve aspect ratio.
        """
        if pixmap.isNull():
            return
        
        # Adjust size to fit with padding
        padding = 4
        new_width = pixmap.width() + (padding * 2)
        new_height = pixmap.height() + (padding * 2)
        
        pixmap = pixmap.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.setPixmap(pixmap)
        self.update()