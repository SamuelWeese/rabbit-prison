"""
Game world containing walls and characters
"""

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from character import Character, CharacterType
from rabbit import Rabbit
from item import Item, Shotgun, Key
from block import Block, BlockType


class Wall:
    """Represents a wall in the game world"""
    def __init__(self, x, y, width, height):
        self.rect = QRectF(x, y, width, height)
        
    def draw(self, painter: QPainter):
        """Draw the wall"""
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawRect(self.rect)


class GameWorld:
    """Manages the game world including walls and characters"""
    def __init__(self):
        self.width = 2000
        self.height = 2000
        
        # Create walls (prison cells and boundaries)
        self.walls = []
        self._create_walls()
        
        # Create placed blocks list (must be before _create_characters)
        self.placed_blocks = []
        
        # Create characters
        self.characters = []
        self._create_characters()
        
        # Create items
        self.items = []
        self._create_items()
        
        # Create bullets list
        self.bullets = []
        
    def _create_walls(self):
        """Create the initial wall layout"""
        # No walls at the beginning - empty world
        pass
        
    def _create_characters(self):
        """Create initial characters (warden and rabbits)"""
        # Create the warden (player character) - start in an open area
        warden = Character(1000, 500, CharacterType.WARDEN)
        self.characters.append(warden)
        
        # Create some rabbit prisoners
        rabbit_positions = [
            (150, 150),   # Cell 1
            (370, 150),   # Cell 2
            (590, 150),   # Cell 3
            (150, 370),   # Cell 4
            (370, 370),   # Cell 5
            (590, 370),   # Cell 6
        ]
        
        import random
        for x, y in rabbit_positions:
            rabbit = Rabbit(x, y)
            # Initialize needs with some variation
            rabbit.food_level = random.uniform(50, 100)
            rabbit.water_level = random.uniform(50, 100)
            rabbit.sleep_level = random.uniform(50, 100)
            self.characters.append(rabbit)
            
        # Add some food and water blocks to the world
        self._create_facilities()
            
    def _create_items(self):
        """Create items in the world"""
        # Add some keys scattered around
        key_positions = [
            (500, 300),
            (800, 400),
            (1200, 600),
        ]
        
        for x, y in key_positions:
            key = Key(x, y)
            self.items.append(key)
            
    def _create_facilities(self):
        """Create food and water facilities in the world"""
        # Add food blocks in common areas
        food_positions = [
            (300, 300),
            (700, 300),
            (1100, 300),
        ]
        
        # Add water blocks
        water_positions = [
            (500, 500),
            (900, 500),
        ]
        
        for x, y in food_positions:
            food_block = Block(x, y, BlockType.FOOD)
            self.placed_blocks.append(food_block)
            
        for x, y in water_positions:
            water_block = Block(x, y, BlockType.WATER)
            self.placed_blocks.append(water_block)
            
    def get_size(self):
        """Get the world dimensions"""
        return self.width, self.height
        
    def get_warden(self):
        """Get the warden character"""
        for character in self.characters:
            if character.character_type == CharacterType.WARDEN:
                return character
        return None
        
    def check_collision(self, character: Character, dx, dy):
        """Check if moving the character by dx, dy would cause a collision"""
        # Calculate new position
        new_x = character.x + dx
        new_y = character.y + dy
        
        # Create a test rect at the new position
        test_rect = QRectF(new_x - character.size // 2, 
                          new_y - character.size // 2, 
                          character.size, character.size)
        
        # Check collision with walls
        for wall in self.walls:
            if test_rect.intersects(wall.rect):
                return True
                
        # Check collision with placed blocks (doors don't block when open, food/water/farm don't block)
        for block in self.placed_blocks:
            if block.block_type == BlockType.DOOR and block.is_open:
                continue  # Open doors don't block
            if (block.block_type == BlockType.FOOD or 
                block.block_type == BlockType.WATER or 
                block.block_type == BlockType.FARM):
                continue  # Food, water, and farm blocks don't block movement
            if test_rect.intersects(block.get_rect()):
                return True
                
        # Check world bounds
        if (new_x - character.size // 2 < 0 or 
            new_x + character.size // 2 > self.width or
            new_y - character.size // 2 < 0 or 
            new_y + character.size // 2 > self.height):
            return True
            
        return False
        
    def update_farms(self, delta_time):
        """Update all farm blocks growth"""
        for block in self.placed_blocks:
            if block.block_type == BlockType.FARM:
                block.update_growth(delta_time)
    
    def draw(self, painter: QPainter):
        """Draw the entire world"""
        # Draw floor grid for reference
        self._draw_grid(painter)
        
        # Draw walls
        for wall in self.walls:
            wall.draw(painter)
        
        # Draw non-blocking placed blocks (farms, food, water) before characters
        # so characters appear on top when walking on them
        for block in self.placed_blocks:
            if (block.block_type == BlockType.FARM or 
                block.block_type == BlockType.FOOD or 
                block.block_type == BlockType.WATER):
                block.draw(painter)
            
        # Draw characters (appear on top of non-blocking blocks)
        for character in self.characters:
            character.draw(painter)
            
        # Draw items (only if not held)
        for item in self.items:
            if item.held_by is None:
                # Draw item on ground
                item.draw(painter, item.x, item.y, 0, 0)
                
        # Draw bullets
        for bullet in self.bullets:
            if bullet.active:
                bullet.draw(painter)
                
        # Draw blocking placed blocks (walls, doors) after characters
        for block in self.placed_blocks:
            if (block.block_type == BlockType.WALL or 
                block.block_type == BlockType.DOOR):
                block.draw(painter)
    
    def draw_interaction_highlights(self, painter: QPainter, warden):
        """Draw highlights around interactive objects near the warden"""
        if not warden:
            return
        
        interactive_objects = self.get_interactive_objects_near(warden.x, warden.y, 50)
        
        for obj_type, obj in interactive_objects:
            # Draw highlight outline
            painter.setPen(QPen(QColor(255, 255, 0), 3))  # Yellow highlight
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))  # No fill
            
            if obj_type == 'door':
                # Highlight door block
                block = obj
                highlight_margin = 3
                painter.drawRect(int(block.x - highlight_margin), 
                               int(block.y - highlight_margin),
                               block.size + highlight_margin * 2,
                               block.size + highlight_margin * 2)
            elif obj_type == 'item':
                # Highlight item (small circle)
                item = obj
                highlight_radius = 15
                painter.drawEllipse(int(item.x - highlight_radius),
                                  int(item.y - highlight_radius),
                                  highlight_radius * 2,
                                  highlight_radius * 2)
            elif obj_type == 'farm':
                # Highlight harvestable farm
                block = obj
                highlight_margin = 3
                painter.drawRect(int(block.x - highlight_margin),
                               int(block.y - highlight_margin),
                               block.size + highlight_margin * 2,
                               block.size + highlight_margin * 2)
                
    def update_bullets(self):
        """Update all bullets"""
        bullets_to_remove = []
        for bullet in self.bullets:
            bullet.update()
            # Check if bullet is out of bounds
            if (bullet.x < 0 or bullet.x > self.width or 
                bullet.y < 0 or bullet.y > self.height):
                bullets_to_remove.append(bullet)
            # Check collision with walls
            bullet_rect = bullet.get_rect()
            for wall in self.walls:
                if bullet_rect.intersects(wall.rect):
                    bullets_to_remove.append(bullet)
                    break
        # Remove inactive bullets
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)
                
    def place_block(self, x, y, block_type: BlockType, warden=None):
        """Place a block at the given position (snapped to grid)"""
        # Snap to grid
        block_size = 50
        snapped_x = (x // block_size) * block_size
        snapped_y = (y // block_size) * block_size
        
        # Check if placing a farm - requires 1 carrot
        if block_type == BlockType.FARM:
            if not warden or warden.carrots < 1:
                return False  # Not enough carrots
            warden.carrots -= 1  # Deduct 1 carrot
        
        # Check if position is already occupied by another block
        new_block_rect = QRectF(snapped_x, snapped_y, block_size, block_size)
        for existing_block in self.placed_blocks:
            if new_block_rect.intersects(existing_block.get_rect()):
                return False  # Position already occupied by a block
        
        # Check if position is occupied by a character (all block types)
        for character in self.characters:
            char_rect = character.get_rect()
            if new_block_rect.intersects(char_rect):
                return False  # Position occupied by a character
        
        # Create and place block
        block = Block(snapped_x, snapped_y, block_type)
        self.placed_blocks.append(block)
        return True
        
    def remove_block(self, x, y):
        """Remove a block at the given position"""
        block_size = 50
        snapped_x = (x // block_size) * block_size
        snapped_y = (y // block_size) * block_size
        
        for block in self.placed_blocks:
            if block.x == snapped_x and block.y == snapped_y:
                self.placed_blocks.remove(block)
                return True
        return False
        
    def toggle_door(self, x, y):
        """Toggle a door at the given position (open/close)"""
        block_size = 50
        snapped_x = (x // block_size) * block_size
        snapped_y = (y // block_size) * block_size
        
        for block in self.placed_blocks:
            if block.block_type == BlockType.DOOR:
                if block.x == snapped_x and block.y == snapped_y:
                    was_open = block.is_open
                    block.is_open = not block.is_open
                    
                    # If closing the door, push objects out of the way
                    if was_open and not block.is_open:
                        self._push_objects_from_door(block)
                    
                    return True
        return False
        
    def _find_closest_free_space(self, door_block, start_x, start_y):
        """Find the closest free space to move an object to"""
        block_size = 50
        door_rect = door_block.get_rect()
        door_center_x = door_block.x + door_block.size // 2
        door_center_y = door_block.y + door_block.size // 2
        
        # Search in expanding circles around the door
        max_search_radius = 200
        search_step = block_size
        
        for radius in range(search_step, max_search_radius, search_step):
            # Check positions in a circle around the door
            for angle in range(0, 360, 45):  # Check 8 directions
                import math
                check_x = door_center_x + math.cos(math.radians(angle)) * radius
                check_y = door_center_y + math.sin(math.radians(angle)) * radius
                
                # Snap to grid
                snapped_x = (int(check_x) // block_size) * block_size
                snapped_y = (int(check_y) // block_size) * block_size
                
                # Check if this position is free
                test_rect = QRectF(snapped_x, snapped_y, block_size, block_size)
                
                # Check collision with walls
                collides = False
                for wall in self.walls:
                    if test_rect.intersects(wall.rect):
                        collides = True
                        break
                
                if collides:
                    continue
                
                # Check collision with placed blocks (except the door we're closing)
                for placed_block in self.placed_blocks:
                    if placed_block == door_block:
                        continue
                    if placed_block.block_type == BlockType.DOOR and placed_block.is_open:
                        continue  # Open doors don't block
                    if (placed_block.block_type == BlockType.FOOD or 
                        placed_block.block_type == BlockType.WATER or 
                        placed_block.block_type == BlockType.FARM):
                        continue  # Food, water, and farm blocks don't block
                    if test_rect.intersects(placed_block.get_rect()):
                        collides = True
                        break
                
                if not collides:
                    return snapped_x + block_size // 2, snapped_y + block_size // 2
        
        # If no free space found, push to a direction away from door center
        import math
        dx = start_x - door_center_x
        dy = start_y - door_center_y
        if dx == 0 and dy == 0:
            # Object is exactly at center, push north
            return door_center_x, door_center_y - block_size
        # Normalize direction
        distance = (dx**2 + dy**2)**0.5
        if distance > 0:
            push_x = door_center_x + (dx / distance) * block_size * 2
            push_y = door_center_y + (dy / distance) * block_size * 2
            return push_x, push_y
        return door_center_x, door_center_y - block_size
        
    def _push_objects_from_door(self, door_block):
        """Push all objects out of a door's space when closing"""
        door_rect = door_block.get_rect()
        block_size = 50
        
        # Push characters
        for character in self.characters:
            char_rect = character.get_rect()
            if char_rect.intersects(door_rect):
                # Find closest free space
                new_x, new_y = self._find_closest_free_space(door_block, character.x, character.y)
                character.x = new_x
                character.y = new_y
        
        # Push items
        for item in self.items:
            if item.held_by is None:  # Only push items not being held
                item_rect = QRectF(item.x - 5, item.y - 5, 10, 10)  # Small rect for items
                if item_rect.intersects(door_rect):
                    new_x, new_y = self._find_closest_free_space(door_block, item.x, item.y)
                    item.x = new_x
                    item.y = new_y
        
        # Remove bullets that are in the door (they get destroyed)
        bullets_to_remove = []
        for bullet in self.bullets:
            if bullet.active:
                bullet_rect = bullet.get_rect()
                if bullet_rect.intersects(door_rect):
                    bullets_to_remove.append(bullet)
        
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)
        
    def get_nearby_door(self, x, y, max_distance=40):
        """Get a door near the given position"""
        for block in self.placed_blocks:
            if block.block_type == BlockType.DOOR:
                # Calculate distance to door center
                door_center_x = block.x + block.size // 2
                door_center_y = block.y + block.size // 2
                dx = door_center_x - x
                dy = door_center_y - y
                distance = (dx**2 + dy**2)**0.5
                if distance <= max_distance:
                    return block
        return None
        
    def find_nearest_food_block(self, x, y, max_distance=500):
        """Find the nearest food block"""
        nearest = None
        min_distance = max_distance
        
        for block in self.placed_blocks:
            if block.block_type == BlockType.FOOD:
                block_center_x = block.x + block.size // 2
                block_center_y = block.y + block.size // 2
                dx = block_center_x - x
                dy = block_center_y - y
                distance = (dx**2 + dy**2)**0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest = block
        return nearest
        
    def find_nearest_water_block(self, x, y, max_distance=500):
        """Find the nearest water block"""
        nearest = None
        min_distance = max_distance
        
        for block in self.placed_blocks:
            if block.block_type == BlockType.WATER:
                block_center_x = block.x + block.size // 2
                block_center_y = block.y + block.size // 2
                dx = block_center_x - x
                dy = block_center_y - y
                distance = (dx**2 + dy**2)**0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest = block
        return nearest
        
    def is_at_facility(self, character, facility_block):
        """Check if character is close enough to interact with facility"""
        if not facility_block:
            return False
        facility_x, facility_y = facility_block.get_interaction_point()
        dx = facility_x - character.x
        dy = facility_y - character.y
        distance = (dx**2 + dy**2)**0.5
        return distance < 30  # Close enough to interact
    
    def get_interactive_objects_near(self, x, y, max_distance=50):
        """Get all interactive objects near a position"""
        interactive = []
        
        # Check for nearby doors
        door = self.get_nearby_door(x, y, max_distance)
        if door:
            interactive.append(('door', door))
        
        # Check for nearby items on ground
        for item in self.items:
            if item.held_by is None:
                dx = item.x - x
                dy = item.y - y
                distance = (dx**2 + dy**2)**0.5
                if distance <= max_distance:
                    interactive.append(('item', item))
        
        # Check for harvestable farms
        for block in self.placed_blocks:
            if block.block_type == BlockType.FARM and block.is_harvestable():
                block_center_x = block.x + block.size // 2
                block_center_y = block.y + block.size // 2
                dx = block_center_x - x
                dy = block_center_y - y
                distance = (dx**2 + dy**2)**0.5
                if distance <= max_distance:
                    interactive.append(('farm', block))
        
        return interactive
    
    def get_nearby_harvestable_farm(self, x, y, max_distance=50):
        """Get a harvestable farm near the given position"""
        for block in self.placed_blocks:
            if block.block_type == BlockType.FARM and block.is_harvestable():
                block_center_x = block.x + block.size // 2
                block_center_y = block.y + block.size // 2
                dx = block_center_x - x
                dy = block_center_y - y
                distance = (dx**2 + dy**2)**0.5
                if distance <= max_distance:
                    return block
        return None
    
    def find_nearest_harvestable_farm(self, x, y, max_distance=500):
        """Find the nearest harvestable farm for rabbits"""
        nearest = None
        min_distance = max_distance
        
        for block in self.placed_blocks:
            if block.block_type == BlockType.FARM and block.is_harvestable():
                block_center_x = block.x + block.size // 2
                block_center_y = block.y + block.size // 2
                dx = block_center_x - x
                dy = block_center_y - y
                distance = (dx**2 + dy**2)**0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest = block
        return nearest
            
    def _draw_grid(self, painter: QPainter):
        """Draw a grid on the floor for reference"""
        grid_size = 50
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        
        # Draw vertical lines
        for x in range(0, self.width, grid_size):
            painter.drawLine(x, 0, x, self.height)
            
        # Draw horizontal lines
        for y in range(0, self.height, grid_size):
            painter.drawLine(0, y, self.width, y)

