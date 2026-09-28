"""Particle background widget for ambient animation."""
from __future__ import annotations
import random
import math
from typing import List

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPen


class Particle:
    """Single particle with position, velocity, and appearance."""
    
    def __init__(self, width: int, height: int):
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.2, 0.2)
        self.radius = random.uniform(2.0, 4.0)
        self.alpha = random.randint(30, 80)
        self.color_index = random.randint(0, 3)
    
    def update(self, width: int, height: int):
        """Update particle position with wrapping."""
        self.x += self.vx
        self.y += self.vy
        
        # Wrap around edges
        if self.x < -self.radius:
            self.x = width + self.radius
        elif self.x > width + self.radius:
            self.x = -self.radius
        
        if self.y < -self.radius:
            self.y = height + self.radius
        elif self.y > height + self.radius:
            self.y = -self.radius


class ParticleWidget(QWidget):
    """Widget that renders animated particles as ambient background."""
    
    # Color palette - burgundy theme variations
    PARTICLE_COLORS = [
        QColor(139, 26, 58),   # #8b1a3a
        QColor(201, 79, 124),  # #c94f7c
        QColor(74, 13, 42),    # #4a0d2a
        QColor(168, 58, 90),   # #a83a5a
    ]
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("ParticleWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        
        # Initialize particles
        self._particles: List[Particle] = []
        self._init_particles()
        
        # Animation timer - 30fps
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_particles)
        self._timer.start(33)  # ~30fps
    
    def _init_particles(self):
        """Initialize particle pool."""
        size = self.size()
        width = max(size.width(), 800)
        height = max(size.height(), 600)
        self._particles = [Particle(width, height) for _ in range(50)]
    
    def resizeEvent(self, event):
        """Reinitialize particles on resize."""
        super().resizeEvent(event)
        self._init_particles()
    
    def _update_particles(self):
        """Update all particle positions."""
        width = self.width()
        height = self.height()
        
        if width <= 0 or height <= 0:
            return
        
        for particle in self._particles:
            particle.update(width, height)
        
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Render all particles."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for particle in self._particles:
            color = self.PARTICLE_COLORS[particle.color_index]
            color.setAlpha(particle.alpha)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            painter.drawEllipse(
                QPoint(int(particle.x), int(particle.y)),
                int(particle.radius),
                int(particle.radius)
            )