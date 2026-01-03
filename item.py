"""
Items that can be held and used by characters
"""

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
import math


class ItemType:
    """Item types"""
    SHOTGUN = "shotgun"
    KEY = "key"
    TOOL = "tool"


class Item:
    """Base class for items"""
    def __init__(self, item_type, x=0, y=0):
        self.item_type = item_type
        self.x = x
        self.y = y
        self.held_by = None  # Character holding this item
        
    def get_grip_positions(self, holder_x, holder_y, aim_angle):
        """Get positions where hands should grip the item
        Returns: (fore_hand_x, fore_hand_y, rear_hand_x, rear_hand_y)
        """
        # Default: both hands at center
        grip_offset = 5
        fore_hand_x = holder_x + math.cos(aim_angle) * grip_offset
        fore_hand_y = holder_y + math.sin(aim_angle) * grip_offset
        rear_hand_x = holder_x - math.cos(aim_angle) * grip_offset
        rear_hand_y = holder_y - math.sin(aim_angle) * grip_offset
        return fore_hand_x, fore_hand_y, rear_hand_x, rear_hand_y
        
    def use(self, holder):
        """Use the item"""
        pass
        
    def draw(self, painter: QPainter, x, y, angle, current_frame=0):
        """Draw the item"""
        pass


class Shotgun(Item):
    """A shotgun that can be held and pointed"""
    def __init__(self, x=0, y=0):
        super().__init__(ItemType.SHOTGUN, x, y)
        self.length = 30
        self.width = 4
        self.stock_length = 10
        self.last_fired_frame = -100
        
    def get_grip_positions(self, holder_x, holder_y, aim_angle):
        """Get the positions where hands should grip the shotgun"""
        # Fore hand (left hand) - near the front of the barrel (positive offset)
        fore_grip_offset = (self.length + 8) * 0.6  # Near the front of the barrel
        fore_hand_x = holder_x + math.cos(aim_angle) * fore_grip_offset
        fore_hand_y = holder_y + math.sin(aim_angle) * fore_grip_offset
        
        # Rear hand (right hand) - near the stock/trigger (negative offset)
        rear_grip_offset = -(self.stock_length + 4)  # Near the stock
        rear_hand_x = holder_x + math.cos(aim_angle) * rear_grip_offset
        rear_hand_y = holder_y + math.sin(aim_angle) * rear_grip_offset
        
        return fore_hand_x, fore_hand_y, rear_hand_x, rear_hand_y
        
    def use(self, holder):
        """Fire the shotgun - returns a bullet if fired"""
        self.last_fired_frame = holder.frame_count
        # Create bullet at muzzle position
        muzzle_offset = self.length + 8 + 4  # barrel length + receiver + tip
        bullet_x = holder.x + math.cos(holder.aim_angle) * muzzle_offset
        bullet_y = holder.y + math.sin(holder.aim_angle) * muzzle_offset
        from bullet import Bullet
        return Bullet(bullet_x, bullet_y, holder.aim_angle)
        
    def draw(self, painter: QPainter, x, y, angle, current_frame=0):
        """Draw the shotgun"""
        painter.save()
        painter.translate(x, y)
        # Rotate to point in the direction (gun barrel points in positive X direction)
        painter.rotate(math.degrees(angle))
        
        # Draw stock (wooden brown with grain effect) - on the left side
        painter.setPen(QPen(QColor(60, 40, 25), 2))
        painter.setBrush(QBrush(QColor(101, 67, 33)))
        painter.drawRect(-self.stock_length, -self.width // 2 - 1, 
                        self.stock_length, self.width + 2)
        # Stock grain lines
        painter.setPen(QPen(QColor(80, 50, 30), 1))
        for i in range(2):
            grain_y = -self.width // 2 + (i + 1) * (self.width + 2) // 3
            painter.drawLine(-self.stock_length, grain_y, 0, grain_y)
        
        # Draw receiver/action (dark metal with highlights)
        painter.setPen(QPen(QColor(20, 20, 20), 2))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        receiver_length = 8
        painter.drawRect(0, -self.width // 2 - 1, 
                        receiver_length, self.width + 2)
        # Receiver highlight
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawLine(0, -self.width // 2, 
                        receiver_length, -self.width // 2)
        
        # Draw shotgun barrel (dark metal) - points to the right
        painter.setPen(QPen(QColor(35, 35, 35), 2))
        painter.setBrush(QBrush(QColor(55, 55, 55)))
        painter.drawRect(receiver_length, -self.width // 2, self.length, self.width)
        
        # Barrel highlight
        painter.setPen(QPen(QColor(75, 75, 75), 1))
        painter.drawLine(receiver_length, -self.width // 2, 
                        receiver_length + self.length, -self.width // 2)
        
        # Draw barrel tip (muzzle) - at the end of the barrel
        painter.setPen(QPen(QColor(30, 30, 30), 2))
        painter.setBrush(QBrush(QColor(35, 35, 35)))
        tip_length = 4
        muzzle_x = receiver_length + self.length
        painter.drawRect(muzzle_x, -self.width // 2, tip_length, self.width)
        
        # Draw trigger guard
        painter.setPen(QPen(QColor(25, 25, 25), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        trigger_y = self.width // 2 + 3
        trigger_guard_width = 7
        trigger_guard_height = 6
        trigger_x = receiver_length // 2
        painter.drawRoundedRect(trigger_x - trigger_guard_width // 2, 
                               trigger_y - 2, 
                               trigger_guard_width, trigger_guard_height, 
                               2, 2)
        
        # Draw trigger
        painter.setPen(QPen(QColor(45, 45, 45), 1))
        painter.setBrush(QBrush(QColor(65, 65, 65)))
        painter.drawRect(trigger_x - 1, trigger_y, 2, 4)
        
        # Draw pump action handle (if visible)
        pump_x = int(receiver_length + self.length * 0.4)
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawRect(pump_x, -self.width // 2 - 3, 4, self.width + 6)
        
        # Draw muzzle flash if recently fired - at the muzzle end
        frames_since_fire = current_frame - self.last_fired_frame
        if frames_since_fire < 5:
            # Calculate flash intensity (fades over time)
            intensity = 1.0 - (frames_since_fire / 5.0)
            flash_base_size = 12
            flash_size = int(flash_base_size * intensity)
            flash_x = muzzle_x + tip_length  # Flash comes out of the muzzle
            
            # Outer flash - bright yellow/orange
            painter.setPen(QPen(QColor(255, 255, 0, int(255 * intensity)), 1))
            painter.setBrush(QBrush(QColor(255, 255, 100, int(200 * intensity))))
            painter.drawEllipse(flash_x - flash_size // 2, -flash_size // 2, flash_size, flash_size)
            
            # Middle flash - orange
            mid_size = int(flash_size * 0.7)
            painter.setBrush(QBrush(QColor(255, 180, 0, int(220 * intensity))))
            painter.drawEllipse(flash_x - mid_size // 2, -mid_size // 2, mid_size, mid_size)
            
            # Inner flash - bright white/yellow
            inner_size = int(flash_size * 0.4)
            painter.setBrush(QBrush(QColor(255, 255, 200, int(255 * intensity))))
            painter.drawEllipse(flash_x - inner_size // 2, -inner_size // 2, inner_size, inner_size)
            
            # Muzzle smoke particles
            if frames_since_fire < 3:
                painter.setPen(QPen(QColor(100, 100, 100, int(150 * intensity)), 1))
                painter.setBrush(QBrush(QColor(120, 120, 120, int(100 * intensity))))
                # Draw several smoke particles
                for i in range(3):
                    particle_x = flash_x - flash_size // 2 + (i - 1) * 3
                    particle_y = -flash_size // 2 + (i % 2) * 2
                    particle_size = 2 + (i % 2)
                    painter.drawEllipse(particle_x, particle_y, particle_size, particle_size)
        
        painter.restore()


class Key(Item):
    """A key item"""
    def __init__(self, x=0, y=0):
        super().__init__(ItemType.KEY, x, y)
        self.size = 8
        
    def get_grip_positions(self, holder_x, holder_y, aim_angle):
        """Key is held in one hand"""
        grip_offset = 3
        hand_x = holder_x + math.cos(aim_angle) * grip_offset
        hand_y = holder_y + math.sin(aim_angle) * grip_offset
        # Return same position for both hands (key held in one)
        return hand_x, hand_y, hand_x, hand_y
        
    def use(self, holder):
        """Use the key (doesn't create bullets)"""
        return None  # Keys don't shoot
        
    def draw(self, painter: QPainter, x, y, angle, current_frame=0):
        """Draw the key"""
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(angle))
        
        # Draw key head (circular)
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.setBrush(QBrush(QColor(255, 215, 0)))  # Gold
        painter.drawEllipse(-self.size // 2, -self.size // 2, self.size, self.size)
        
        # Draw key shaft
        painter.setBrush(QBrush(QColor(200, 180, 0)))
        painter.drawRect(-self.size // 2, 0, 2, self.size)
        
        # Draw key teeth
        painter.setBrush(QBrush(QColor(200, 180, 0)))
        painter.drawRect(-self.size // 2 + 1, self.size, 1, 2)
        painter.drawRect(-self.size // 2 - 1, self.size + 2, 1, 2)
        
        painter.restore()

