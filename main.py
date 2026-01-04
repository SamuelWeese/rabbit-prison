#!/usr/bin/env python3
"""
Rabbit Prison - A game where you play as the warden managing rabbit prisoners
"""

import sys
from assets import SpriteCache
from PyQt5.QtWidgets import QApplication
from game_window import GameWindow


def main():
    app = QApplication(sys.argv)
    SpriteCache.load()
    window = GameWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

