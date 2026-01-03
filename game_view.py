"""
2D game view with movable camera, walls, and characters
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QKeyEvent, QPen, QBrush, QMouseEvent
from game_world import GameWorld
from character import Character, CharacterType
from rabbit import Rabbit
from item import Shotgun, Key
from hotbar import Hotbar
from block import BlockItem, BlockType
import math
import random


class GameView(QWidget):
    def __init__(self):
        super().__init__()
        self.world = GameWorld()
        
        # Camera position (top-left corner of visible area)
        self.camera_x = 0
        self.camera_y = 0
        
        # Camera movement speed
        self.camera_speed = 5
        
        # Keys currently pressed
        self.keys_pressed = set()
        
        # Set up game loop timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # ~60 FPS
        
        # Set minimum size
        self.setMinimumSize(800, 600)
        
        # Mouse tracking for aiming
        self.setMouseTracking(True)
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Create hotbar
        self.hotbar = Hotbar(self.width(), self.height())
        
        # Give warden a shotgun to start and add to hotbar
        warden = self.world.get_warden()
        if warden:
            shotgun = Shotgun()
            self.hotbar.set_slot(0, shotgun)
            warden.equip_item(shotgun)
            
        # Add some keys to hotbar slots
        key1 = Key()
        self.hotbar.set_slot(1, key1)
        
        # Add block items to hotbar (concrete wall, door, food, water)
        self.hotbar.set_slot(2, BlockItem(BlockType.WALL))
        self.hotbar.set_slot(3, BlockItem(BlockType.DOOR))
        self.hotbar.set_slot(4, BlockItem(BlockType.FOOD))
        self.hotbar.set_slot(5, BlockItem(BlockType.WATER))
        
    def update_game(self):
        """Update game state and camera position"""
        warden = self.world.get_warden()
        if not warden:
            return
        
        # Increment frame count every frame (for muzzle flash animation)
        warden.frame_count += 1
            
        # Move warden based on pressed keys
        dx = 0
        dy = 0
        
        if Qt.Key_W in self.keys_pressed or Qt.Key_Up in self.keys_pressed:
            dy = -warden.speed
        if Qt.Key_S in self.keys_pressed or Qt.Key_Down in self.keys_pressed:
            dy = warden.speed
        if Qt.Key_A in self.keys_pressed or Qt.Key_Left in self.keys_pressed:
            dx = -warden.speed
        if Qt.Key_D in self.keys_pressed or Qt.Key_Right in self.keys_pressed:
            dx = warden.speed
        
        # Check collision before moving
        if dx != 0 or dy != 0:
            # Try moving in X direction first
            if dx != 0 and not self.world.check_collision(warden, dx, 0):
                warden.move(dx, 0)
            # Then try moving in Y direction
            if dy != 0 and not self.world.check_collision(warden, 0, dy):
                warden.move(0, dy)
        
        # Update aim angle based on mouse position
        world_mouse_x = self.mouse_x + self.camera_x
        world_mouse_y = self.mouse_y + self.camera_y
        warden.set_aim_angle(world_mouse_x, world_mouse_y)
        
        # Update bullets
        self.world.update_bullets()
        
        # Update rabbit AI - handle needs and movement
        delta_time = 0.016  # ~60 FPS
        world_width, world_height = self.world.get_size()
        
        for character in self.world.characters:
            if isinstance(character, Rabbit):
                # Update needs
                character.update_needs(delta_time)
                
                # Handle current action (eating, drinking, sleeping)
                if character.is_eating or character.is_drinking:
                    continue  # Don't move while eating/drinking
                if character.is_sleeping:
                    # Rabbits stay still while sleeping until fully rested
                    continue  # Don't move while sleeping
                
                # Check needs and seek facilities
                target_x = None
                target_y = None
                should_seek_facility = False
                
                # Check if needs food
                if character.food_level < 30:
                    food_block = self.world.find_nearest_food_block(character.x, character.y)
                    if food_block:
                        if self.world.is_at_facility(character, food_block):
                            character.target_facility = food_block
                            character.start_eating()
                            # Reset random movement when starting to eat
                            character.random_target_x = None
                            character.random_target_y = None
                            character.is_waiting = False
                        else:
                            target_x, target_y = food_block.get_interaction_point()
                            should_seek_facility = True
                            # Reset random movement when seeking food
                            character.random_target_x = None
                            character.random_target_y = None
                            character.is_waiting = False
                
                # Check if needs water (higher priority if very low)
                if character.water_level < 30:
                    water_block = self.world.find_nearest_water_block(character.x, character.y)
                    if water_block:
                        if self.world.is_at_facility(character, water_block):
                            character.target_facility = water_block
                            character.start_drinking()
                            # Reset random movement when starting to drink
                            character.random_target_x = None
                            character.random_target_y = None
                            character.is_waiting = False
                        else:
                            target_x, target_y = water_block.get_interaction_point()
                            should_seek_facility = True
                            # Reset random movement when seeking water
                            character.random_target_x = None
                            character.random_target_y = None
                            character.is_waiting = False
                
                # Check if needs sleep
                if character.sleep_level < 20 and not should_seek_facility:
                    # Find a safe spot to sleep (away from player)
                    sleep_x = character.x + (character.x - warden.x) * 0.3
                    sleep_y = character.y + (character.y - warden.y) * 0.3
                    # Clamp to world bounds
                    sleep_x = max(50, min(sleep_x, world_width - 50))
                    sleep_y = max(50, min(sleep_y, world_height - 50))
                    
                    # Check if at sleep location
                    dx = sleep_x - character.x
                    dy = sleep_y - character.y
                    if (dx**2 + dy**2)**0.5 < 20:
                        character.start_sleeping()
                        # Reset random movement when starting to sleep
                        character.random_target_x = None
                        character.random_target_y = None
                        character.is_waiting = False
                    else:
                        target_x = sleep_x
                        target_y = sleep_y
                        # Reset random movement when seeking sleep spot
                        character.random_target_x = None
                        character.random_target_y = None
                        character.is_waiting = False
                
                # Random movement behavior (only when not seeking facilities)
                if not should_seek_facility and character.sleep_level >= 20:
                    # Handle waiting timer
                    if character.is_waiting:
                        character.wait_timer -= delta_time
                        if character.wait_timer <= 0:
                            character.is_waiting = False
                            # Pick a new random target within a shorter distance (50-150 pixels away)
                            angle = random.uniform(0, 2 * math.pi)
                            distance = random.uniform(50, 150)
                            character.random_target_x = character.x + math.cos(angle) * distance
                            character.random_target_y = character.y + math.sin(angle) * distance
                            # Clamp to world bounds
                            character.random_target_x = max(50, min(character.random_target_x, world_width - 50))
                            character.random_target_y = max(50, min(character.random_target_y, world_height - 50))
                    else:
                        # Check if we have a target
                        if character.random_target_x is None or character.random_target_y is None:
                            # Pick a new random target within a shorter distance (50-150 pixels away)
                            angle = random.uniform(0, 2 * math.pi)
                            distance = random.uniform(50, 150)
                            character.random_target_x = character.x + math.cos(angle) * distance
                            character.random_target_y = character.y + math.sin(angle) * distance
                            # Clamp to world bounds
                            character.random_target_x = max(50, min(character.random_target_x, world_width - 50))
                            character.random_target_y = max(50, min(character.random_target_y, world_height - 50))
                        
                        # Move towards random target
                        dx = character.random_target_x - character.x
                        dy = character.random_target_y - character.y
                        distance = (dx**2 + dy**2)**0.5
                        
                        # Check if reached target
                        if distance < 15:  # Close enough
                            # Start waiting
                            character.is_waiting = True
                            character.wait_timer = random.uniform(1.0, 3.0)  # Wait 1-3 seconds
                            character.random_target_x = None
                            character.random_target_y = None
                        else:
                            # Move towards target
                            character.move_towards(character.random_target_x, character.random_target_y, self.world)
                else:
                    # Seek facility or sleep spot
                    if target_x is not None and target_y is not None:
                        character.move_towards(target_x, target_y, self.world)
        
        # Check for item pickup (if player is near an item)
        pickup_distance = 30
        for item in self.world.items:
            if item.held_by is None:
                dx = item.x - warden.x
                dy = item.y - warden.y
                distance = (dx**2 + dy**2)**0.5
                if distance < pickup_distance:
                    # Pick up the item
                    old_item = warden.held_item
                    warden.equip_item(item)
                    # If player had an item, drop it
                    if old_item:
                        old_item.x = warden.x
                        old_item.y = warden.y
                        old_item.held_by = None
                    break
        
        # Make camera follow the warden (centered on warden)
        view_width = self.width()
        view_height = self.height()
        self.camera_x = warden.x - view_width // 2
        self.camera_y = warden.y - view_height // 2
        
        # Clamp camera to world bounds
        world_width, world_height = self.world.get_size()
        self.camera_x = max(0, min(self.camera_x, world_width - view_width))
        self.camera_y = max(0, min(self.camera_y, world_height - view_height))
        
        self.update()  # Trigger repaint
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events"""
        # Handle spacebar for opening/closing doors
        if event.key() == Qt.Key_Space:
            warden = self.world.get_warden()
            if warden:
                # Check for nearby door (works with any item or empty hands)
                nearby_door = self.world.get_nearby_door(warden.x, warden.y)
                if nearby_door:
                    self.world.toggle_door(nearby_door.x, nearby_door.y)
            event.accept()
            return
        
        # Handle number keys for hotbar selection (1-9)
        if Qt.Key_1 <= event.key() <= Qt.Key_9:
            slot_index = event.key() - Qt.Key_1
            self.hotbar.select_slot(slot_index)
            # Equip the selected item (or None if slot is empty)
            selected_item = self.hotbar.get_selected_item()
            warden = self.world.get_warden()
            if warden:
                warden.equip_item(selected_item)  # Can be None to clear hands
            event.accept()
            return
        
        # Handle scroll wheel for hotbar (mouse wheel already handled)
        if event.key() == Qt.Key_Tab:
            # Shift+Tab for previous, Tab for next (simplified - just Tab for next)
            self.hotbar.select_next()
            selected_item = self.hotbar.get_selected_item()
            warden = self.world.get_warden()
            if warden:
                warden.equip_item(selected_item)  # Can be None to clear hands
            event.accept()
            return
            
        self.keys_pressed.add(event.key())
        event.accept()
        
    def keyReleaseEvent(self, event: QKeyEvent):
        """Handle key release events"""
        self.keys_pressed.discard(event.key())
        event.accept()
        
    def paintEvent(self, event):
        """Paint the game world"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(200, 200, 200))
        
        # Translate to camera position
        painter.translate(-self.camera_x, -self.camera_y)
        
        # Draw world
        self.world.draw(painter)
        
        # Reset translation for UI elements
        painter.resetTransform()
        
        # Draw hotbar
        self.hotbar.draw(painter, self.width(), self.height())
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Track mouse position for aiming"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        event.accept()
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks"""
        warden = self.world.get_warden()
        
        if event.button() == Qt.LeftButton:
            if warden and warden.held_item:
                # Check if holding a block item
                if hasattr(warden.held_item, 'get_block_type'):
                    # Place block
                    world_x = self.mouse_x + self.camera_x
                    world_y = self.mouse_y + self.camera_y
                    block_type = warden.held_item.get_block_type()
                    self.world.place_block(world_x, world_y, block_type)
                else:
                    # Use regular item (shoot, etc.)
                    bullet = warden.use_item()
                    if bullet:
                        self.world.bullets.append(bullet)
        elif event.button() == Qt.RightButton:
            # Right click to remove blocks
            world_x = self.mouse_x + self.camera_x
            world_y = self.mouse_y + self.camera_y
            self.world.remove_block(world_x, world_y)
            
        event.accept()
        
    def wheelEvent(self, event):
        """Handle mouse wheel for hotbar scrolling"""
        # Scroll through hotbar slots
        if event.angleDelta().y() > 0:
            # Scroll up - previous slot
            self.hotbar.select_prev()
        else:
            # Scroll down - next slot
            self.hotbar.select_next()
        
        # Equip the selected item (or None if slot is empty)
        selected_item = self.hotbar.get_selected_item()
        warden = self.world.get_warden()
        if warden:
            warden.equip_item(selected_item)  # Can be None to clear hands
        event.accept()

