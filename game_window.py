"""
Main game window and view
"""

from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QKeyEvent
from game_view import GameView


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rabbit Prison - Warden Mode")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create the game view
        self.game_view = GameView()
        self.setCentralWidget(self.game_view)
        
        # Set focus to receive keyboard events
        self.game_view.setFocusPolicy(Qt.StrongFocus)
        self.game_view.setFocus()

