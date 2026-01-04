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
        
        # FPS counter
        self.frame_times = []
        self.fps = 0
        self.last_fps_update = 0
        
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
        
        # Add block items to hotbar (concrete wall, door, food, water, farm)
        self.hotbar.set_slot(2, BlockItem(BlockType.WALL))
        self.hotbar.set_slot(3, BlockItem(BlockType.DOOR))
        self.hotbar.set_slot(4, BlockItem(BlockType.FOOD))
        self.hotbar.set_slot(5, BlockItem(BlockType.WATER))
        self.hotbar.set_slot(6, BlockItem(BlockType.FARM))
        
    def update_game(self):
        """Update game state and camera position"""
        # Calculate FPS
        import time
        current_time = time.time()
        if hasattr(self, 'last_frame_time'):
            frame_time = current_time - self.last_frame_time
            self.frame_times.append(frame_time)
            # Keep only last 60 frames for averaging
            if len(self.frame_times) > 60:
                self.frame_times.pop(0)
            # Update FPS every 0.5 seconds
            if current_time - self.last_fps_update > 0.5:
                if self.frame_times:
                    avg_frame_time = sum(self.frame_times) / len(self.frame_times)
                    self.fps = int(1.0 / avg_frame_time) if avg_frame_time > 0 else 0
                self.last_fps_update = current_time
        self.last_frame_time = current_time
        
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
        
        # Update farm growth
        delta_time = 0.016  # ~60 FPS
        self.world.update_farms(delta_time)
        
        # Update rabbit AI - handle needs and movement
        delta_time = 0.016  # ~60 FPS
        world_width, world_height = self.world.get_size()
        
        for character in self.world.characters:
            if isinstance(character, Rabbit):
                # Check for farm destruction BEFORE update_needs (which resets state when timer hits 0)
                if character.is_eating and character.target_facility:
                    # Check if target is a farm block
                    if (hasattr(character.target_facility, 'block_type') and 
                        character.target_facility.block_type == BlockType.FARM):
                        # Check if eating animation is done (timer will be decremented by update_needs)
                        # Store reference before update_needs potentially resets it
                        farm_to_remove = character.target_facility
                        timer_before = character.action_timer
                        
                        # Update needs (this will decrement the timer)
                        character.update_needs(delta_time)
                        
                        # Check if timer just finished (was > 0, now <= 0)
                        if timer_before > 0 and character.action_timer <= 0:
                            # Completely destroy the farm block
                            if farm_to_remove in self.world.placed_blocks:
                                self.world.placed_blocks.remove(farm_to_remove)
                            # Also try removing by position to be sure
                            self.world.remove_block(farm_to_remove.x, farm_to_remove.y)
                            # Restore food level
                            character.food_level = min(100, character.food_level + 30)
                            character.is_eating = False
                            character.target_facility = None
                            continue
                        # Still eating - don't move
                        continue
                
                
                # Update needs for non-farm eating, non-breeding
                character.update_needs(delta_time)
                
                # Handle current action (eating, drinking, sleeping, breeding)
                # Note: Farm eating is handled above, so skip if already handled
                if character.is_eating and character.target_facility and hasattr(character.target_facility, 'block_type') and character.target_facility.block_type == BlockType.FARM:
                    continue  # Farm eating already handled above
                if character.is_eating or character.is_drinking:
                    continue  # Don't move while eating/drinking
                if character.is_sleeping:
                    # Rabbits stay still while sleeping until fully rested
                    continue  # Don't move while sleeping
                # Handle breeding mode - rabbit seeks a partner
                if character.is_breeding:
                    # Find a breeding partner if we don't have one
                    if character.breeding_partner is None:
                        # Look for another rabbit that is also in breeding mode
                        closest_partner = None
                        closest_distance = float('inf')
                        for other_rabbit in self.world.characters:
                            if (isinstance(other_rabbit, Rabbit) and 
                                other_rabbit != character and
                                other_rabbit.is_breeding):
                                # Check if this rabbit is also looking for a partner
                                # (not already paired with someone else)
                                if other_rabbit.breeding_partner is None or other_rabbit.breeding_partner == character:
                                    dx = other_rabbit.x - character.x
                                    dy = other_rabbit.y - character.y
                                    distance = math.sqrt(dx**2 + dy**2)
                                    if distance < closest_distance:
                                        closest_distance = distance
                                        closest_partner = other_rabbit
                        
                        if closest_partner:
                            character.breeding_partner = closest_partner
                            # Make sure the partner also knows about us (bidirectional pairing)
                            if closest_partner.breeding_partner != character:
                                closest_partner.breeding_partner = character
                    
                    # If we have a partner, move towards them
                    if character.breeding_partner:
                        # Check if partner is still valid (still in breeding mode and exists)
                        if (character.breeding_partner not in self.world.characters or
                            not character.breeding_partner.is_breeding):
                            # Partner left breeding mode or was removed, reset
                            character.breeding_partner = None
                            continue
                        
                        # Move towards partner
                        partner_x = character.breeding_partner.x
                        partner_y = character.breeding_partner.y
                        dx = partner_x - character.x
                        dy = partner_y - character.y
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        # If close enough (within 30 pixels), complete breeding
                        if distance < 30:
                            # Both rabbits complete breeding
                            character.is_breeding = False
                            character.breeding_cooldown = 30.0
                            if character.breeding_partner:
                                character.breeding_partner.is_breeding = False
                                character.breeding_partner.breeding_cooldown = 30.0
                                character.breeding_partner.breeding_partner = None
                            character.breeding_partner = None
                            
                            # Spawn new rabbit between the two parents
                            new_rabbit_x = (character.x + partner_x) / 2
                            new_rabbit_y = (character.y + partner_y) / 2
                            # Create new rabbit
                            new_rabbit = Rabbit(new_rabbit_x, new_rabbit_y)
                            new_rabbit.food_level = random.uniform(50, 100)
                            new_rabbit.water_level = random.uniform(50, 100)
                            new_rabbit.sleep_level = random.uniform(50, 100)
                            new_rabbit.health = 100
                            self.world.characters.append(new_rabbit)
                            
                            # Reset random movement
                            character.random_target_x = None
                            character.random_target_y = None
                            character.is_waiting = False
                            continue
                        else:
                            # Move towards partner
                            character.move_towards(partner_x, partner_y, self.world)
                            continue
                    else:
                        # No partner found yet, keep looking (stay in breeding mode)
                        # Could add some random movement here while searching
                        continue
                
                # Check breeding conditions FIRST (before other actions)
                # Full health and 75%+ food, no cooldown, not sleeping
                if (character.health >= 100 and 
                    character.food_level >= 75 and 
                    character.breeding_cooldown <= 0 and
                    character.sleep_level >= 20):
                    # Random chance to start breeding (5% chance per frame when conditions met)
                    if random.random() < 0.05:
                        character.start_breeding()
                        continue
                
                # Check needs and seek facilities
                target_x = None
                target_y = None
                should_seek_facility = False
                
                # Always check for harvestable farms (carrots) - rabbits eat them regardless of hunger
                harvestable_farm = self.world.find_nearest_harvestable_farm(character.x, character.y, 500)
                if harvestable_farm:
                    farm_center_x = harvestable_farm.x + harvestable_farm.size // 2
                    farm_center_y = harvestable_farm.y + harvestable_farm.size // 2
                    dx = farm_center_x - character.x
                    dy = farm_center_y - character.y
                    distance = (dx**2 + dy**2)**0.5
                    
                    # Check if close enough to eat (within 30 pixels)
                    if distance < 30:
                        # Start eating animation (3 seconds for farms)
                        character.start_eating(duration=3.0)
                        character.target_facility = harvestable_farm
                        # Reset random movement
                        character.random_target_x = None
                        character.random_target_y = None
                        character.is_waiting = False
                    else:
                        # Move towards the farm
                        target_x = farm_center_x
                        target_y = farm_center_y
                        should_seek_facility = True
                        # Reset random movement
                        character.random_target_x = None
                        character.random_target_y = None
                        character.is_waiting = False
                # Check if needs food (only if no harvestable farms available)
                elif character.food_level < 30:
                    # No harvestable farms, check for food blocks
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
        # Handle spacebar for opening/closing doors and harvesting farms
        if event.key() == Qt.Key_Space:
            warden = self.world.get_warden()
            if warden:
                # Check for nearby harvestable farm first
                nearby_farm = self.world.get_nearby_harvestable_farm(warden.x, warden.y, 50)
                if nearby_farm:
                    # Harvest the farm
                    if nearby_farm.harvest():
                        import random
                        # Give random amount of carrots (1-5)
                        carrots_gained = random.randint(1, 5)
                        warden.carrots += carrots_gained
                else:
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
        
        # Draw interaction highlights (after world, before UI)
        warden = self.world.get_warden()
        if warden:
            self.world.draw_interaction_highlights(painter, warden)
        
        # Reset translation for UI elements
        painter.resetTransform()
        
        # Draw FPS counter (top right)
        self._draw_fps(painter)
        
        # Draw resources UI (top left)
        self._draw_resources(painter)
        
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
            if warden:
                if warden.held_item:
                    # Check if holding a block item
                    if hasattr(warden.held_item, 'get_block_type'):
                        # Place block
                        world_x = self.mouse_x + self.camera_x
                        world_y = self.mouse_y + self.camera_y
                        block_type = warden.held_item.get_block_type()
                        self.world.place_block(world_x, world_y, block_type, warden)
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
    
    def _draw_resources(self, painter: QPainter):
        """Draw resource display (carrots, money, rabbit meat, rabbit poop) and rabbit counter vertically in top left"""
        warden = self.world.get_warden()
        if not warden:
            return
        
        # Count rabbits
        rabbit_count = sum(1 for char in self.world.characters if isinstance(char, Rabbit))
        
        # Background panel
        panel_width = 100
        panel_height = 135  # Increased to fit rabbit counter
        panel_x = 10
        panel_y = 10
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QBrush(QColor(50, 50, 50, 200)))
        painter.drawRoundedRect(panel_x, panel_y, panel_width, panel_height, 5, 5)
        
        # Set font and color for text
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)
        
        # Vertical spacing between resources
        line_height = 25
        start_x = panel_x + 10
        start_y = panel_y + 20
        
        # Draw carrots
        painter.drawText(start_x, start_y, "🥕")
        painter.drawText(start_x + 25, start_y, f"{warden.carrots}")
        
        # Draw money
        painter.drawText(start_x, start_y + line_height, "💰")
        painter.drawText(start_x + 25, start_y + line_height, f"{warden.money}")
        
        # Draw rabbit meat
        painter.drawText(start_x, start_y + line_height * 2, "🥩")
        painter.drawText(start_x + 25, start_y + line_height * 2, f"{warden.rabbit_meat}")
        
        # Draw rabbit poop
        painter.drawText(start_x, start_y + line_height * 3, "💩")
        painter.drawText(start_x + 25, start_y + line_height * 3, f"{warden.rabbit_poop}")
        
        # Draw rabbit counter
        painter.drawText(start_x, start_y + line_height * 4, "🐰")
        painter.drawText(start_x + 25, start_y + line_height * 4, f"{rabbit_count}")
    
    def _draw_fps(self, painter: QPainter):
        """Draw FPS counter in top right corner"""
        # Set font and color for FPS
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        # Draw FPS text
        fps_text = f"FPS: {self.fps}"
        text_width = painter.fontMetrics().width(fps_text)
        fps_x = self.width() - text_width - 15
        fps_y = 25
        
        # Draw background
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRoundedRect(fps_x - 5, fps_y - 15, text_width + 10, 20, 3, 3)
        
        # Draw FPS text
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawText(fps_x, fps_y, fps_text)

