"""
Block system for building structures
"""

from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from enum import Enum


class BlockType(Enum):
    WALL = "wall"  # Concrete wall
    DOOR = "door"
    FOOD = "food"
    WATER = "water"
    FARM = "farm"  # Farm plot that grows food
    FENCE = "fence"  # Farm fence


class Block:
    """A placeable block for building"""
    def __init__(self, x, y, block_type: BlockType):
        self.x = x
        self.y = y
        self.block_type = block_type
        self.size = 50  # Block size in pixels
        self.is_open = False  # For doors - whether they're open
        
        # Farm growth system
        if block_type == BlockType.FARM:
            self.growth_stage = 0  # 0 = empty, 1 = planted, 2 = growing, 3 = ready
            self.growth_timer = 0.0
            self.growth_time = 10.0  # Time in seconds to fully grow
        
    def get_rect(self):
        """Get bounding rectangle"""
        return QRectF(self.x, self.y, self.size, self.size)
        
    def get_interaction_point(self):
        """Get the point where a character should stand to interact"""
        return self.x + self.size // 2, self.y + self.size // 2
        
    def draw(self, painter: QPainter):
        """Draw the block"""
        if self.block_type == BlockType.WALL:
            # Draw wall block (gray stone)
            painter.setPen(QPen(QColor(80, 80, 80), 2))
            painter.setBrush(QBrush(QColor(120, 120, 120)))
            painter.drawRect(int(self.x), int(self.y), self.size, self.size)
            # Add stone texture lines
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawLine(int(self.x + 10), int(self.y), int(self.x + 10), int(self.y + self.size))
            painter.drawLine(int(self.x), int(self.y + 10), int(self.x + self.size), int(self.y + 10))
            
        elif self.block_type == BlockType.DOOR:
            if self.is_open:
                # Draw open door - see-through (only frame visible)
                # Door frame (always visible, darker)
                painter.setPen(QPen(QColor(60, 40, 20), 3))
                painter.setBrush(QBrush(QColor(80, 50, 30, 200)))  # Semi-transparent frame
                # Draw frame outline
                painter.drawRect(int(self.x), int(self.y), self.size, self.size)
                # Inner frame (lighter, more transparent)
                painter.setPen(QPen(QColor(100, 70, 40, 150), 2))
                painter.setBrush(QBrush(QColor(0, 0, 0, 0)))  # Completely transparent interior
                painter.drawRect(int(self.x + 3), int(self.y + 3), self.size - 6, self.size - 6)
                # Door handle (still visible when open)
                painter.setPen(QPen(QColor(200, 200, 200), 2))
                painter.setBrush(QBrush(QColor(200, 200, 200)))
                painter.drawEllipse(int(self.x + self.size - 8), int(self.y + self.size // 2 - 3), 6, 6)
            else:
                # Draw closed door (brown with handle)
                painter.setPen(QPen(QColor(80, 50, 30), 2))
                painter.setBrush(QBrush(QColor(101, 67, 33)))
                painter.drawRect(int(self.x), int(self.y), self.size, self.size)
                # Door frame
                painter.setPen(QPen(QColor(60, 40, 20), 2))
                painter.setBrush(QBrush(QColor(0, 0, 0, 0)))  # No fill
                painter.drawRect(int(self.x + 2), int(self.y + 2), self.size - 4, self.size - 4)
                # Door handle
                painter.setPen(QPen(QColor(200, 200, 200), 2))
                painter.setBrush(QBrush(QColor(200, 200, 200)))
                painter.drawEllipse(int(self.x + self.size - 12), int(self.y + self.size // 2 - 3), 6, 6)
                
        elif self.block_type == BlockType.FOOD:
            # Draw food block (table with food)
            # Table
            painter.setPen(QPen(QColor(101, 67, 33), 2))
            painter.setBrush(QBrush(QColor(139, 90, 43)))
            painter.drawRect(int(self.x), int(self.y + self.size - 8), self.size, 8)
            # Food items (apples, bread)
            # Apple 1
            painter.setPen(QPen(QColor(200, 50, 50), 1))
            painter.setBrush(QBrush(QColor(255, 100, 100)))
            painter.drawEllipse(int(self.x + 8), int(self.y + 10), 10, 10)
            # Apple 2
            painter.drawEllipse(int(self.x + 22), int(self.y + 12), 10, 10)
            # Bread
            painter.setPen(QPen(QColor(200, 150, 100), 1))
            painter.setBrush(QBrush(QColor(222, 184, 135)))
            painter.drawRect(int(self.x + 35), int(self.y + 10), 12, 8)
            
        elif self.block_type == BlockType.WATER:
            # Draw water block (fountain/water source)
            # Base
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.setBrush(QBrush(QColor(150, 150, 150)))
            painter.drawRect(int(self.x), int(self.y + self.size - 10), self.size, 10)
            # Water basin
            painter.setPen(QPen(QColor(80, 150, 255), 2))
            painter.setBrush(QBrush(QColor(100, 180, 255, 200)))
            painter.drawRect(int(self.x + 5), int(self.y + 5), self.size - 10, self.size - 15)
            # Water surface (wavy)
            painter.setPen(QPen(QColor(150, 200, 255), 1))
            for i in range(3):
                wave_y = int(self.y + 8 + i * 2)
                painter.drawLine(int(self.x + 8), wave_y, int(self.x + self.size - 8), wave_y)
            # Spout/faucet
            painter.setPen(QPen(QColor(120, 120, 120), 2))
            painter.setBrush(QBrush(QColor(140, 140, 140)))
            painter.drawRect(int(self.x + self.size // 2 - 3), int(self.y + 2), 6, 6)
            
        elif self.block_type == BlockType.FARM:
            # Draw farm plot with growth stages
            # Soil/dirt base
            painter.setPen(QPen(QColor(101, 67, 33), 2))
            painter.setBrush(QBrush(QColor(139, 90, 43)))
            painter.drawRect(int(self.x), int(self.y), self.size, self.size)
            
            # Draw soil texture (lines)
            painter.setPen(QPen(QColor(101, 67, 33), 1))
            for i in range(3):
                painter.drawLine(int(self.x + i * 15), int(self.y), 
                               int(self.x + i * 15), int(self.y + self.size))
            
            # Draw growth based on stage
            if self.growth_stage == 0:
                # Empty plot - just show soil
                pass
            elif self.growth_stage == 1:
                # Planted - small seed/sprout
                painter.setPen(QPen(QColor(50, 150, 50), 1))
                painter.setBrush(QBrush(QColor(100, 200, 100)))
                # Small sprout
                painter.drawEllipse(int(self.x + self.size // 2 - 2), 
                                  int(self.y + self.size - 8), 4, 4)
            elif self.growth_stage == 2:
                # Growing - medium plant
                painter.setPen(QPen(QColor(50, 150, 50), 2))
                painter.setBrush(QBrush(QColor(100, 200, 100)))
                # Stem
                painter.drawRect(int(self.x + self.size // 2 - 1), 
                               int(self.y + self.size - 15), 2, 10)
                # Leaves
                painter.drawEllipse(int(self.x + self.size // 2 - 4), 
                                  int(self.y + self.size - 12), 8, 6)
            elif self.growth_stage == 3:
                # Ready to harvest - full plant with food
                painter.setPen(QPen(QColor(50, 150, 50), 2))
                painter.setBrush(QBrush(QColor(100, 200, 100)))
                # Stem
                painter.drawRect(int(self.x + self.size // 2 - 1), 
                               int(self.y + self.size - 20), 2, 15)
                # Large leaves
                painter.drawEllipse(int(self.x + self.size // 2 - 6), 
                                  int(self.y + self.size - 18), 12, 8)
                # Food items (carrots/vegetables)
                painter.setPen(QPen(QColor(255, 150, 0), 1))
                painter.setBrush(QBrush(QColor(255, 200, 0)))
                # Carrot 1
                painter.drawEllipse(int(self.x + self.size // 2 - 8), 
                                  int(self.y + self.size - 8), 6, 8)
                # Carrot 2
                painter.drawEllipse(int(self.x + self.size // 2 + 2), 
                                  int(self.y + self.size - 8), 6, 8)
        
        elif self.block_type == BlockType.FENCE:
            # Draw fence (wooden picket fence style)
            # Wood color
            wood_color = QColor(139, 90, 43)
            dark_wood = QColor(101, 67, 33)
            
            # Background (slightly lighter)
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.setBrush(QBrush(QColor(150, 110, 60)))
            painter.drawRect(int(self.x), int(self.y), self.size, self.size)
            
            # Draw pickets (vertical slats)
            picket_width = 6
            picket_spacing = 8
            num_pickets = 3
            start_x = self.x + (self.size - (num_pickets * picket_width + (num_pickets - 1) * picket_spacing)) // 2
            
            for i in range(num_pickets):
                picket_x = int(start_x + i * (picket_width + picket_spacing))
                # Picket post
                painter.setPen(QPen(dark_wood, 1))
                painter.setBrush(QBrush(wood_color))
                painter.drawRect(picket_x, int(self.y), picket_width, self.size)
                # Picket top (pointed)
                points = [
                    QPointF(picket_x, self.y),
                    QPointF(picket_x + picket_width // 2, self.y - 4),
                    QPointF(picket_x + picket_width, self.y)
                ]
                painter.drawPolygon(points)
            
            # Horizontal rails
            painter.setPen(QPen(dark_wood, 2))
            painter.setBrush(QBrush(wood_color))
            # Top rail
            painter.drawRect(int(self.x), int(self.y + 8), self.size, 3)
            # Bottom rail
            painter.drawRect(int(self.x), int(self.y + self.size - 11), self.size, 3)
    
    def update_growth(self, delta_time):
        """Update farm growth over time"""
        if self.block_type == BlockType.FARM:
            if self.growth_stage == 0:
                # Auto-plant when empty (after a short delay)
                self.growth_timer += delta_time
                if self.growth_timer >= 1.0:  # 1 second delay before auto-planting
                    self.growth_stage = 1
                    self.growth_timer = 0.0
            elif self.growth_stage < 3:
                # Grow over time
                self.growth_timer += delta_time
                growth_progress = self.growth_timer / self.growth_time
                
                if growth_progress < 0.33:
                    self.growth_stage = 1  # Planted
                elif growth_progress < 0.66:
                    self.growth_stage = 2  # Growing
                else:
                    self.growth_stage = 3  # Ready
    
    def harvest(self):
        """Harvest the farm - resets growth and returns True if harvestable"""
        if self.block_type == BlockType.FARM and self.growth_stage == 3:
            self.growth_stage = 0
            self.growth_timer = 0.0
            return True
        return False
    
    def is_harvestable(self):
        """Check if the farm is ready to harvest"""
        return self.block_type == BlockType.FARM and self.growth_stage == 3


class BlockItem:
    """An item that represents a block type for placement"""
    def __init__(self, block_type: BlockType):
        self.block_type = block_type
        self.item_type = "block"  # For hotbar compatibility
        
    def get_block_type(self):
        """Get the block type this item represents"""
        return self.block_type
        
    def get_interaction_point(self):
        """Get the point where a character should stand to interact"""
        return self.x + self.size // 2, self.y + self.size // 2
        
    def get_grip_positions(self, holder_x, holder_y, aim_angle):
        """Get positions where hands should grip the block item"""
        import math
        # Block items are held in front of the character
        grip_offset = 8
        hand_x = holder_x + math.cos(aim_angle) * grip_offset
        hand_y = holder_y + math.sin(aim_angle) * grip_offset
        # Both hands hold the block together
        return hand_x, hand_y, hand_x, hand_y
        
    def draw(self, painter, x, y, angle, current_frame=0):
        """Draw a preview of the block being held"""
        # Draw a small preview block
        preview_size = 20
        if self.block_type == BlockType.WALL:
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.setBrush(QBrush(QColor(120, 120, 120)))
            painter.drawRect(int(x - preview_size // 2), int(y - preview_size // 2), 
                           preview_size, preview_size)
        elif self.block_type == BlockType.DOOR:
            painter.setPen(QPen(QColor(80, 50, 30), 1))
            painter.setBrush(QBrush(QColor(101, 67, 33)))
            painter.drawRect(int(x - preview_size // 2), int(y - preview_size // 2), 
                           preview_size, preview_size)
        elif self.block_type == BlockType.FOOD:
            painter.setPen(QPen(QColor(200, 50, 50), 1))
            painter.setBrush(QBrush(QColor(255, 100, 100)))
            painter.drawEllipse(int(x - preview_size // 2), int(y - preview_size // 2), 
                               preview_size, preview_size)
        elif self.block_type == BlockType.WATER:
            painter.setPen(QPen(QColor(80, 150, 255), 1))
            painter.setBrush(QBrush(QColor(100, 180, 255)))
            painter.drawRect(int(x - preview_size // 2), int(y - preview_size // 2), 
                           preview_size, preview_size)
        elif self.block_type == BlockType.FARM:
            painter.setPen(QPen(QColor(101, 67, 33), 1))
            painter.setBrush(QBrush(QColor(139, 90, 43)))
            painter.drawRect(int(x - preview_size // 2), int(y - preview_size // 2), 
                           preview_size, preview_size)

