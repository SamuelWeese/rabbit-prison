"""
Hotbar UI for item selection (Minecraft-style)
"""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from item import Item, ItemType
from block import BlockType


class Hotbar:
    """Minecraft-style hotbar for item selection"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.slots = [None] * 9  # 9 slots like Minecraft
        self.selected_slot = 0  # Currently selected slot (0-8)
        self.slot_size = 50
        self.slot_spacing = 4
        
    def set_slot(self, index, item):
        """Set an item in a slot"""
        if 0 <= index < 9:
            self.slots[index] = item
            
    def get_selected_item(self):
        """Get the currently selected item"""
        return self.slots[self.selected_slot]
        
    def select_slot(self, index):
        """Select a slot by index (0-8)"""
        if 0 <= index < 9:
            self.selected_slot = index
            
    def select_next(self):
        """Select next slot"""
        self.selected_slot = (self.selected_slot + 1) % 9
        
    def select_prev(self):
        """Select previous slot"""
        self.selected_slot = (self.selected_slot - 1) % 9
        
    def draw(self, painter: QPainter, view_width, view_height):
        """Draw the hotbar at the bottom center of the screen"""
        # Calculate hotbar position (centered at bottom)
        total_width = (self.slot_size + self.slot_spacing) * 9 - self.slot_spacing
        start_x = (view_width - total_width) // 2
        start_y = view_height - self.slot_size - 20
        
        # Draw background (semi-transparent dark bar)
        bg_height = self.slot_size + 10
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRoundedRect(start_x - 5, start_y - 5, 
                               total_width + 10, bg_height, 
                               5, 5)
        
        # Draw slots
        for i in range(9):
            slot_x = start_x + i * (self.slot_size + self.slot_spacing)
            slot_y = start_y
            
            # Draw slot background
            if i == self.selected_slot:
                # Selected slot - highlighted border
                painter.setPen(QPen(QColor(255, 255, 255), 3))
                painter.setBrush(QBrush(QColor(100, 100, 100, 200)))
            else:
                # Unselected slot
                painter.setPen(QPen(QColor(150, 150, 150), 2))
                painter.setBrush(QBrush(QColor(50, 50, 50, 200)))
            
            painter.drawRoundedRect(slot_x, slot_y, 
                                   self.slot_size, self.slot_size, 
                                   3, 3)
            
            # Draw item in slot
            item = self.slots[i]
            if item:
                # Draw item icon (simplified - just a colored square for now)
                icon_margin = 8
                icon_x = slot_x + icon_margin
                icon_y = slot_y + icon_margin
                icon_size = self.slot_size - icon_margin * 2
                
                # Check if it's a block item
                if hasattr(item, 'get_block_type'):
                    block_type = item.get_block_type()
                    if block_type == BlockType.WALL:
                        painter.setPen(QPen(QColor(80, 80, 80), 2))
                        painter.setBrush(QBrush(QColor(120, 120, 120)))
                        painter.drawRect(icon_x, icon_y, icon_size, icon_size)
                    elif block_type == BlockType.DOOR:
                        painter.setPen(QPen(QColor(80, 50, 30), 2))
                        painter.setBrush(QBrush(QColor(101, 67, 33)))
                        painter.drawRect(icon_x, icon_y, icon_size, icon_size)
                    elif block_type == BlockType.FOOD:
                        painter.setPen(QPen(QColor(200, 50, 50), 1))
                        painter.setBrush(QBrush(QColor(255, 100, 100)))
                        painter.drawEllipse(icon_x, icon_y, icon_size, icon_size)
                    elif block_type == BlockType.WATER:
                        painter.setPen(QPen(QColor(80, 150, 255), 1))
                        painter.setBrush(QBrush(QColor(100, 180, 255)))
                        painter.drawRect(icon_x, icon_y, icon_size, icon_size)
                elif hasattr(item, 'item_type'):
                    if item.item_type == ItemType.SHOTGUN:
                        # Draw shotgun icon (simplified)
                        painter.setPen(QPen(QColor(60, 60, 60), 2))
                        painter.setBrush(QBrush(QColor(80, 80, 80)))
                        # Barrel
                        painter.drawRect(icon_x, icon_y + icon_size // 3, 
                                       icon_size, icon_size // 3)
                        # Stock
                        painter.setBrush(QBrush(QColor(101, 67, 33)))
                        painter.drawRect(icon_x - icon_size // 4, icon_y + icon_size // 3, 
                                       icon_size // 4, icon_size // 3)
                    elif item.item_type == ItemType.KEY:
                        # Draw key icon
                        painter.setPen(QPen(QColor(200, 200, 0), 2))
                        painter.setBrush(QBrush(QColor(255, 215, 0)))
                        painter.drawEllipse(icon_x, icon_y, icon_size // 2, icon_size // 2)
                        painter.drawRect(icon_x + icon_size // 4, icon_y + icon_size // 2, 
                                       2, icon_size // 2)
            
            # Draw slot number (1-9)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawText(slot_x + self.slot_size - 15, 
                           slot_y + self.slot_size - 5, 
                           str(i + 1))

