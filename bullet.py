"""
Bullet system for projectiles
"""

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
import math


class Bullet:
    """A bullet projectile"""
    def __init__(self, x, y, angle, speed=15):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.size = 3
        self.active = True
        
    def update(self):
        """Update bullet position"""
        if self.active:
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
            
    def draw(self, painter: QPainter):
        """Draw the bullet"""
        if self.active:
            painter.setPen(QPen(QColor(200, 200, 0), 1))
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            painter.drawEllipse(int(self.x - self.size // 2), 
                              int(self.y - self.size // 2), 
                              self.size, self.size)
            
    def get_rect(self):
        """Get bounding rectangle"""
        return QRectF(self.x - self.size // 2, 
                     self.y - self.size // 2, 
                     self.size, self.size)

