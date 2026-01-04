"""
Character classes for the game
"""

from enum import Enum
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from item import Item
import math


class CharacterType(Enum):
    WARDEN = "warden"
    RABBIT = "rabbit"


class Character:
    """Represents a character in the game"""
    def __init__(self, x, y, character_type: CharacterType):
        self.x = x
        self.y = y
        self.character_type = character_type
        self.size = 20
        self.speed = 3
        self.held_item = None  # Item currently held
        self.aim_angle = 0  # Angle in radians for aiming
        self.last_dx = 0
        self.last_dy = 0
        self.animation_frame = 0
        self.frame_count = 0
        
        # Resources (only for warden)
        if character_type == CharacterType.WARDEN:
            self.carrots = 10  # Start with 10 carrots
            self.money = 100
            self.rabbit_meat = 0
            self.rabbit_poop = 0
        
    def move(self, dx, dy):
        """Move the character by the given delta"""
        self.x += dx
        self.y += dy
        self.last_dx = dx
        self.last_dy = dy
        if dx != 0 or dy != 0:
            self.animation_frame += 1
        
    def equip_item(self, item: Item):
        """Equip an item"""
        if self.held_item:
            self.held_item.held_by = None
        self.held_item = item
        if item:
            item.held_by = self
            
    def set_aim_angle(self, target_x, target_y):
        """Set the aim angle toward a target point"""
        dx = target_x - self.x
        dy = target_y - self.y
        if dx != 0 or dy != 0:
            self.aim_angle = math.atan2(dy, dx)
            
    def move_towards(self, target_x, target_y, world):
        """Move towards a target, avoiding collisions - moves directly in 2D space"""
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 1:
            return  # Already at target
        
        # Normalize direction and calculate movement vector
        if distance > 0:
            move_dx = (dx / distance) * self.speed
            move_dy = (dy / distance) * self.speed
        else:
            return
        
        # Try to move directly toward target (diagonally if needed)
        if not world.check_collision(self, move_dx, move_dy):
            self.move(move_dx, move_dy)
        else:
            # If diagonal movement blocked, try X only
            if abs(move_dx) > 0.1 and not world.check_collision(self, move_dx, 0):
                self.move(move_dx, 0)
            # Or try Y only
            elif abs(move_dy) > 0.1 and not world.check_collision(self, 0, move_dy):
                self.move(0, move_dy)
            
    def use_item(self):
        """Use the held item - returns bullet if item creates one"""
        if self.held_item:
            return self.held_item.use(self)
        return None
        
    def get_rect(self):
        """Get the bounding rectangle of the character"""
        return QRectF(self.x - self.size // 2, 
                     self.y - self.size // 2, 
                     self.size, self.size)
        
    def draw(self, painter: QPainter):
        """Draw the character"""
        if self.character_type == CharacterType.WARDEN:
            # Draw farmer warden
            center_x = self.x
            center_y = self.y
            half_size = self.size // 2
            
            # Draw body (overalls - denim blue)
            painter.setPen(QPen(QColor(50, 50, 100), 2))
            painter.setBrush(QBrush(QColor(60, 90, 150)))
            body_y = center_y - half_size + 3
            body_height = self.size - 6
            painter.drawRect(center_x - half_size + 2, body_y, 
                           self.size - 4, body_height)
            
            # Draw overall straps
            painter.setPen(QPen(QColor(50, 50, 100), 2))
            painter.setBrush(QBrush(QColor(60, 90, 150)))
            strap_width = 3
            # Left strap
            painter.drawRect(center_x - half_size + 4, body_y, 
                           strap_width, half_size - 2)
            # Right strap
            painter.drawRect(center_x + half_size - 7, body_y, 
                           strap_width, half_size - 2)
            
            # Draw head (skin tone)
            painter.setPen(QPen(QColor(139, 90, 43), 2))
            painter.setBrush(QBrush(QColor(255, 220, 177)))
            head_size = self.size - 6
            head_y = center_y - half_size - 2
            painter.drawEllipse(center_x - head_size // 2, head_y, 
                              head_size, head_size)
            
            # Draw straw hat
            hat_width = self.size + 4
            hat_height = 6
            painter.setPen(QPen(QColor(139, 115, 85), 2))
            painter.setBrush(QBrush(QColor(218, 165, 32)))  # Golden/straw color
            # Hat brim
            painter.drawEllipse(center_x - hat_width // 2, head_y - 2, 
                              hat_width, hat_height)
            # Hat top
            painter.setBrush(QBrush(QColor(184, 134, 11)))  # Darker straw
            painter.drawRect(center_x - hat_width // 2 + 2, head_y - 4, 
                           hat_width - 4, 4)
            
            # Draw simple face (eyes)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            eye_size = 2
            # Left eye
            painter.drawEllipse(center_x - 4, head_y + 4, eye_size, eye_size)
            # Right eye
            painter.drawEllipse(center_x + 2, head_y + 4, eye_size, eye_size)
            
            # Draw arms and hands
            arm_y = body_y + 4
            arm_length = 8
            hand_size = 3
            
            if self.held_item:
                # Holding an item - position hands to grip it
                item_x = center_x
                item_y = center_y + 2
                fore_hand_x, fore_hand_y, rear_hand_x, rear_hand_y = \
                    self.held_item.get_grip_positions(item_x, item_y, self.aim_angle)
                
                # Calculate arm positions to reach grip points
                fore_arm_start_x = center_x - half_size + 3
                fore_arm_start_y = arm_y
                fore_arm_dx = fore_hand_x - fore_arm_start_x
                fore_arm_dy = fore_hand_y - fore_arm_start_y
                fore_arm_length = int(math.sqrt(fore_arm_dx**2 + fore_arm_dy**2))
                fore_arm_angle = math.atan2(fore_arm_dy, fore_arm_dx)
                
                rear_arm_start_x = center_x + half_size - 3
                rear_arm_start_y = arm_y
                rear_arm_dx = rear_hand_x - rear_arm_start_x
                rear_arm_dy = rear_hand_y - rear_arm_start_y
                rear_arm_length = int(math.sqrt(rear_arm_dx**2 + rear_arm_dy**2))
                rear_arm_angle = math.atan2(rear_arm_dy, rear_arm_dx)
                
                # Draw arms (skin tone)
                painter.setPen(QPen(QColor(139, 90, 43), 2))
                painter.setBrush(QBrush(QColor(255, 220, 177)))
                arm_width = 2
                
                # Draw fore arm (left)
                painter.save()
                painter.translate(fore_arm_start_x, fore_arm_start_y)
                painter.rotate(math.degrees(fore_arm_angle))
                painter.drawRect(0, -arm_width // 2, fore_arm_length, arm_width)
                painter.restore()
                
                # Draw rear arm (right)
                painter.save()
                painter.translate(rear_arm_start_x, rear_arm_start_y)
                painter.rotate(math.degrees(rear_arm_angle))
                painter.drawRect(0, -arm_width // 2, rear_arm_length, arm_width)
                painter.restore()
                
                # Draw hands at grip positions
                painter.setBrush(QBrush(QColor(255, 220, 177)))
                painter.drawEllipse(int(fore_hand_x - hand_size // 2), 
                                  int(fore_hand_y - hand_size // 2), 
                                  hand_size, hand_size)
                painter.drawEllipse(int(rear_hand_x - hand_size // 2), 
                                  int(rear_hand_y - hand_size // 2), 
                                  hand_size, hand_size)
                
                # Draw item
                self.held_item.draw(painter, item_x, item_y, self.aim_angle, self.frame_count)
            else:
                # No item - natural walking animation with swinging arms
                # Calculate walking animation phase (0 to 1, cycles)
                walk_phase = (self.animation_frame % 20) / 20.0  # 20 frames per cycle
                
                # Natural arm swing - opposite directions, more pronounced
                # Left arm swings forward when right leg would be forward
                left_swing = math.sin(walk_phase * math.pi * 2) * 6
                right_swing = -left_swing  # Opposite phase
                
                # Vertical swing component (arms move up/down slightly)
                vertical_swing = abs(math.sin(walk_phase * math.pi * 2)) * 2
                
                # Arm base positions
                left_arm_base_x = center_x - half_size + 3
                right_arm_base_x = center_x + half_size - 3
                arm_base_y = arm_y
                
                # Calculate hand positions with natural swing
                left_hand_x = left_arm_base_x - arm_length + left_swing
                left_hand_y = arm_base_y + vertical_swing if left_swing > 0 else arm_base_y - vertical_swing * 0.5
                
                right_hand_x = right_arm_base_x + arm_length + right_swing
                right_hand_y = arm_base_y - vertical_swing if right_swing > 0 else arm_base_y + vertical_swing * 0.5
                
                # Calculate arm angles for natural swing
                left_arm_angle = math.atan2(left_hand_y - arm_base_y, left_hand_x - left_arm_base_x)
                right_arm_angle = math.atan2(right_hand_y - arm_base_y, right_hand_x - right_arm_base_x)
                
                left_arm_length_calc = math.sqrt((left_hand_x - left_arm_base_x)**2 + (left_hand_y - arm_base_y)**2)
                right_arm_length_calc = math.sqrt((right_hand_x - right_arm_base_x)**2 + (right_hand_y - arm_base_y)**2)
                
                # Draw arms (skin tone) with natural angles
                painter.setPen(QPen(QColor(139, 90, 43), 2))
                painter.setBrush(QBrush(QColor(255, 220, 177)))
                arm_width = 2
                
                # Draw left arm
                painter.save()
                painter.translate(left_arm_base_x, arm_base_y)
                painter.rotate(math.degrees(left_arm_angle))
                painter.drawRect(0, -arm_width // 2, int(left_arm_length_calc), arm_width)
                painter.restore()
                
                # Draw right arm
                painter.save()
                painter.translate(right_arm_base_x, arm_base_y)
                painter.rotate(math.degrees(right_arm_angle))
                painter.drawRect(0, -arm_width // 2, int(right_arm_length_calc), arm_width)
                painter.restore()
                
                # Draw hands as open/empty (more detailed)
                painter.setBrush(QBrush(QColor(255, 220, 177)))
                # Left hand - open palm
                painter.drawEllipse(int(left_hand_x - hand_size // 2), 
                                  int(left_hand_y - hand_size // 2), 
                                  hand_size, hand_size)
                # Add fingers indication (small lines)
                painter.setPen(QPen(QColor(200, 180, 150), 1))
                # Thumb
                painter.drawLine(int(left_hand_x - hand_size // 2), 
                               int(left_hand_y), 
                               int(left_hand_x - hand_size // 2 - 2), 
                               int(left_hand_y + 1))
                # Fingers
                for i in range(3):
                    finger_x = int(left_hand_x - hand_size // 2 + 1 + i)
                    painter.drawLine(finger_x, 
                                   int(left_hand_y - hand_size // 2), 
                                   finger_x, 
                                   int(left_hand_y - hand_size // 2 - 2))
                
                # Right hand - open palm
                painter.setBrush(QBrush(QColor(255, 220, 177)))
                painter.setPen(QPen(QColor(139, 90, 43), 2))
                painter.drawEllipse(int(right_hand_x - hand_size // 2), 
                                  int(right_hand_y - hand_size // 2), 
                                  hand_size, hand_size)
                # Add fingers indication
                painter.setPen(QPen(QColor(200, 180, 150), 1))
                # Thumb
                painter.drawLine(int(right_hand_x + hand_size // 2), 
                               int(right_hand_y), 
                               int(right_hand_x + hand_size // 2 + 2), 
                               int(right_hand_y + 1))
                # Fingers
                for i in range(3):
                    finger_x = int(right_hand_x - hand_size // 2 + 1 + i)
                    painter.drawLine(finger_x, 
                                   int(right_hand_y - hand_size // 2), 
                                   finger_x, 
                                   int(right_hand_y - hand_size // 2 - 2))
            
            # Draw boots at bottom
            boot_height = 4
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            painter.setBrush(QBrush(QColor(40, 40, 40)))
            boot_width = 6
            # Left boot
            painter.drawRect(center_x - half_size + 2, 
                           center_y + half_size - boot_height, 
                           boot_width, boot_height)
            # Right boot
            painter.drawRect(center_x + half_size - 8, 
                           center_y + half_size - boot_height, 
                           boot_width, boot_height)

