"""
Rabbit class for the game
"""

from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from character import Character, CharacterType
import math
from assets import SpriteCache


class Rabbit(Character):
    """Represents a rabbit prisoner in the game"""
    def __init__(self, x, y):
        super().__init__(x, y, CharacterType.RABBIT)
        self.speed = 1.0  # Rabbits move slower
        self.size = 50 
        
        # Health and needs system
        self.health = 100.0
        self.food_level = 100.0
        self.water_level = 100.0
        self.sleep_level = 100.0
        self.is_eating = False
        self.is_drinking = False
        self.is_sleeping = False
        self.action_timer = 0.0
        self.target_facility = None  # Food/water block being used
        
        # Random movement system
        self.random_target_x = None
        self.random_target_y = None
        self.wait_timer = 0.0
        self.is_waiting = False
        
        # Breeding system
        self.is_breeding = False
        self.breeding_timer = 0.0
        self.breeding_cooldown = 0.0  # Cooldown between breeding attempts
        self.breeding_partner = None  # Target rabbit to find for breeding
    
    def update_needs(self, delta_time=0.016):
        """Update needs over time"""
        # Decrease needs if not being restored
        if not self.is_eating:
            self.food_level = max(0, self.food_level - 0.5 * delta_time)
        if not self.is_drinking:
            self.water_level = max(0, self.water_level - 0.8 * delta_time)
        if not self.is_sleeping:
            self.sleep_level = max(0, self.sleep_level - 0.3 * delta_time)
        
        # Restore needs while performing actions
        if self.is_eating:
            self.food_level = min(100, self.food_level + 25 * delta_time)  # +25 per second
        if self.is_drinking:
            self.water_level = min(100, self.water_level + 50 * delta_time)  # +50 per second
        if self.is_sleeping:
            self.sleep_level = min(100, self.sleep_level + 20 * delta_time)  # +20 per second
        
        # Update breeding cooldown
        if self.breeding_cooldown > 0:
            self.breeding_cooldown -= delta_time
        
        # Update action timer
        if self.action_timer > 0:
            self.action_timer -= delta_time
            if self.action_timer <= 0:
                # Action complete
                if self.is_eating:
                    self.is_eating = False
                elif self.is_drinking:
                    self.is_drinking = False
                elif self.is_sleeping:
                    # Only wake up if sleep is fully restored
                    if self.sleep_level >= 100:
                        self.is_sleeping = False
                    else:
                        # Continue sleeping - reset timer
                        sleep_needed = 100 - self.sleep_level
                        self.action_timer = sleep_needed / 20.0
                # Breeding is handled differently - no timer, stays until partner found
                if not self.is_sleeping:
                    self.target_facility = None
        
        # Slow down if needs are very low
        if self.food_level < 10 or self.water_level < 10:
            self.speed = 0.5  # Very slow
        elif self.food_level < 30 or self.water_level < 30:
            self.speed = 0.75  # Slow
        else:
            self.speed = 1.0  # Normal rabbit speed
    
    def start_eating(self, duration=2.0):
        """Start eating animation"""
        self.is_eating = True
        self.is_drinking = False
        self.is_sleeping = False
        self.action_timer = duration
    
    def start_drinking(self, duration=1.0):
        """Start drinking animation"""
        self.is_eating = False
        self.is_drinking = True
        self.is_sleeping = False
        self.action_timer = duration
    
    def start_sleeping(self, duration=5.0):
        """Start sleeping animation - rabbits sleep until fully rested"""
        self.is_eating = False
        self.is_drinking = False
        self.is_sleeping = True
        self.is_breeding = False
        # Calculate duration needed to restore sleep to 100
        sleep_needed = 100 - self.sleep_level
        # Sleep restores at 20 per second, so calculate time needed
        self.action_timer = max(duration, sleep_needed / 20.0)
    
    def start_breeding(self):
        """Start breeding mode - rabbit will seek a partner"""
        self.is_eating = False
        self.is_drinking = False
        self.is_sleeping = False
        self.is_breeding = True
        self.breeding_partner = None  # Will be set when finding a partner
        # No timer - stays in breeding mode until partner found
    
    def move_towards(self, target_x, target_y, world):
        """Move towards a target, avoiding collisions - moves directly in 2D space"""
        # Don't move if sleeping - rabbits stay still while sleeping
        if self.is_sleeping:
            return
        # Don't move if eating/drinking (but can move while breeding to find partner)
        if self.is_eating or self.is_drinking:
            return
        
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
    
    def draw(self, painter: QPainter):
        """Draw the rabbit"""
        center_x = self.x
        center_y = self.y
        
        # Animation offset for eating/drinking
        anim_offset_y = 0
        if self.is_eating:
            # Bobbing animation
            anim_offset_y = int(2 * math.sin(self.action_timer * 10))
        elif self.is_drinking:
            # Lean forward
            anim_offset_y = 2
        
        # Draw sleeping rabbit (flattened)
        if self.is_sleeping:
            sprite = SpriteCache.get("rabbit_sleep")
            painter.drawPixmap(int(self.x - self.size // 2), int(self.y - self.size // 3), self.size, self.size, sprite)
        else:
            sprite = SpriteCache.get("rabbit_default")
            painter.drawPixmap(int(self.x - self.size // 2), int(self.y - self.size // 2), self.size, self.size, sprite)
            # Draw action indicators
            if self.is_breeding:
                # Draw hearts above head
                heart_y = int(center_y - self.size // 2 - 15 + anim_offset_y)
                painter.setPen(QPen(QColor(255, 100, 150), 1))
                painter.setBrush(QBrush(QColor(255, 150, 200)))
                # Draw two hearts
                for i in range(2):
                    heart_x = int(center_x - 8 + i * 8)
                    # Simple heart shape (two circles and a triangle)
                    painter.drawEllipse(heart_x - 3, heart_y, 4, 4)
                    painter.drawEllipse(heart_x + 1, heart_y, 4, 4)
                    # Triangle bottom
                    points = [
                        QPointF(heart_x - 3, heart_y + 2),
                        QPointF(heart_x + 5, heart_y + 2),
                        QPointF(heart_x + 1, heart_y + 6)
                    ]
                    painter.drawPolygon(points)
            elif self.is_eating:
                # Draw food icon above head
                food_y = int(center_y - self.size // 2 - 12 + anim_offset_y)
                painter.setPen(QPen(QColor(255, 100, 100), 1))
                painter.setBrush(QBrush(QColor(255, 150, 150)))
                painter.drawEllipse(int(center_x - 4), food_y, 8, 8)
            elif self.is_drinking:
                # Draw water splash
                splash_y = int(center_y - self.size // 2 - 10 + anim_offset_y)
                painter.setPen(QPen(QColor(100, 150, 255), 1))
                painter.setBrush(QBrush(QColor(150, 200, 255, 150)))
                for i in range(3):
                    drop_x = int(center_x - 4 + i * 4)
                    painter.drawEllipse(drop_x, splash_y + i * 2, 3, 3)
        
        # Draw health bar and need indicators above rabbit
        bar_width = 30
        bar_height = 4
        bar_y = int(center_y - self.size // 2 - 30)
        bar_x = int(center_x - bar_width // 2)
        
        # Health bar (green/red based on health)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawRect(bar_x, bar_y, bar_width, bar_height)
        # Health color: green when high, red when low
        health_ratio = self.health / 100.0
        if health_ratio > 0.5:
            health_color = QColor(int(255 * (1 - health_ratio) * 2), 255, 0)  # Green to yellow
        else:
            health_color = QColor(255, int(255 * health_ratio * 2), 0)  # Yellow to red
        painter.setBrush(QBrush(health_color))
        health_width = int(bar_width * health_ratio)
        painter.drawRect(bar_x, bar_y, health_width, bar_height)
        
        # Draw need indicators as circles below health bar
        circle_radius = 4
        circle_spacing = 8
        circle_y = bar_y + bar_height + 4
        start_x = int(center_x - (circle_spacing * 2) / 2)
        
        # Food circle (red)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(start_x - circle_radius, circle_y - circle_radius, 
                          circle_radius * 2, circle_radius * 2)
        # Fill based on food level
        food_fill_radius = int(circle_radius * (self.food_level / 100.0))
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawEllipse(start_x - food_fill_radius, circle_y - food_fill_radius,
                          food_fill_radius * 2, food_fill_radius * 2)
        
        # Water circle (blue)
        water_x = start_x + circle_spacing
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(water_x - circle_radius, circle_y - circle_radius,
                          circle_radius * 2, circle_radius * 2)
        # Fill based on water level
        water_fill_radius = int(circle_radius * (self.water_level / 100.0))
        painter.setBrush(QBrush(QColor(0, 100, 255)))
        painter.drawEllipse(water_x - water_fill_radius, circle_y - water_fill_radius,
                          water_fill_radius * 2, water_fill_radius * 2)
        
        # Sleep circle (purple)
        sleep_x = start_x + circle_spacing * 2
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(sleep_x - circle_radius, circle_y - circle_radius,
                          circle_radius * 2, circle_radius * 2)
        # Fill based on sleep level
        sleep_fill_radius = int(circle_radius * (self.sleep_level / 100.0))
        painter.setBrush(QBrush(QColor(150, 50, 200)))
        painter.drawEllipse(sleep_x - sleep_fill_radius, circle_y - sleep_fill_radius,
                          sleep_fill_radius * 2, sleep_fill_radius * 2)

