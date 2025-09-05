import random
from typing import Optional, Tuple, List
from .brain import CellBrain
from .objects import UniverseObject
from .discovery_system import DISCOVERY_DETECTOR
from .interactions import INTERACTION_ENGINE

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'    # Plants
    YELLOW = '\033[93m'   # Herbivores  
    RED = '\033[91m'      # Carnivores
    RESET = '\033[0m'     # Reset color
    BOLD = '\033[1m'      # Bold text

class Celula:
    def __init__(self, x: int, y: int, brain: CellBrain = None):
        self.x = x
        self.y = y
        self.age = 0
        self.brain = brain if brain else CellBrain()
        self._last_energy = getattr(self, 'energy', 0)
        
        # Discovery and tool system
        self.inventory = []  # Tools and objects this cell has discovered/created
        self.known_discoveries = set()  # IDs of discoveries this cell knows about
        self.experimentation_cooldown = 0  # Prevents constant experimentation
        self.curiosity = random.uniform(0.1, 0.9)  # How likely to experiment
    
    def update(self, world) -> Optional['Celula']:
        """Update cell state and return new cell if reproduction occurs"""
        self.age += 1
        
        # Reduce experimentation cooldown
        if self.experimentation_cooldown > 0:
            self.experimentation_cooldown -= 1
        
        # Try to experiment and discover new things
        self.attempt_discovery(world)
        
        return None
    
    def attempt_discovery(self, world):
        """Attempt to discover new objects through experimentation"""
        if (self.experimentation_cooldown <= 0 and 
            random.random() < self.curiosity and 
            len(self.inventory) >= 2):
            
            # Pick two random objects from inventory to combine
            obj1 = random.choice(self.inventory)
            obj2 = random.choice(self.inventory)
            
            if obj1 != obj2:
                # Attempt interaction
                result = INTERACTION_ENGINE.interact(obj1, obj2, "combine")
                
                if result.success:
                    # Check for discovery
                    discovery = DISCOVERY_DETECTOR.analyze_interaction_result(
                        result, tick=world.step_count, 
                        discoverer_id=f"Cell_{id(self)}"
                    )
                    
                    if discovery and discovery.id not in self.known_discoveries:
                        self.known_discoveries.add(discovery.id)
                        
                        # Add new objects to inventory
                        if result.new_objects:
                            self.inventory.extend(result.new_objects)
                        
                        # Boost brain fitness for making discoveries
                        self.brain.record_energy_gain(10)
                        
                        # Share discovery with nearby cells
                        self.share_discovery_with_neighbors(world, discovery)
                
                # Set cooldown to prevent constant experimentation
                self.experimentation_cooldown = 5
    
    def share_discovery_with_neighbors(self, world, discovery):
        """Share discovery knowledge with adjacent cells"""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                neighbor_x, neighbor_y = self.x + dx, self.y + dy
                
                if (0 <= neighbor_x < world.width and 
                    0 <= neighbor_y < world.height):
                    
                    neighbor = world.grid[neighbor_y][neighbor_x]
                    if (isinstance(neighbor, Celula) and 
                        discovery.id not in neighbor.known_discoveries):
                        neighbor.known_discoveries.add(discovery.id)
                        
                        # Neighbors get some objects too (knowledge sharing)
                        if hasattr(discovery, 'result') and discovery.result.new_objects:
                            for obj in discovery.result.new_objects[:1]:  # Share 1 object
                                neighbor.inventory.append(obj.copy() if hasattr(obj, 'copy') else obj)
    
    def find_basic_materials(self, world):
        """Look for basic materials in the environment to start experimenting"""
        if len(self.inventory) < 3:
            # Check for scattered materials at current position
            if (hasattr(world, 'scattered_materials') and 
                (self.x, self.y) in world.scattered_materials):
                material = world.scattered_materials[(self.x, self.y)]
                self.inventory.append(material)
                del world.scattered_materials[(self.x, self.y)]  # Remove from world
                return
            
            # Check adjacent positions for materials
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    check_x, check_y = self.x + dx, self.y + dy
                    if (0 <= check_x < world.width and 0 <= check_y < world.height):
                        if (hasattr(world, 'scattered_materials') and 
                            (check_x, check_y) in world.scattered_materials and
                            random.random() < 0.3):  # 30% chance to find nearby material
                            material = world.scattered_materials[(check_x, check_y)]
                            self.inventory.append(material)
                            del world.scattered_materials[(check_x, check_y)]
                            return
            
            # Fallback: generate basic materials if none found
            if len(self.inventory) < 2 and random.random() < 0.05:
                basic_materials = [
                    UniverseObject("Piedra", ["es_duro"]),
                    UniverseObject("Palo", ["es_organico", "es_fragil"]),
                    UniverseObject("Hoja", ["es_organico", "es_flexible"])
                ]
                
                material = random.choice(basic_materials)
                self.inventory.append(material)
    
    def should_die(self) -> bool:
        """Check if cell should die"""
        return False
    
    def get_symbol(self) -> str:
        """Return visual representation of cell"""
        return "?"
    
    def get_colored_symbol(self) -> str:
        """Return colored visual representation of cell"""
        return self.get_symbol()

class Planta(Celula):
    def __init__(self, x: int, y: int, reproduction_age: int = 10, max_age: int = 50):
        super().__init__(x, y)
        self.reproduction_age = reproduction_age
        self.max_age = max_age
    
    def update(self, world) -> Optional['Planta']:
        self.age += 1
        
        if self.age >= self.reproduction_age and self.age % self.reproduction_age == 0:
            return self._reproduce(world)
        
        return None
    
    def _reproduce(self, world) -> Optional['Planta']:
        """Attempt to reproduce in adjacent empty cell"""
        adjacent_positions = self._get_adjacent_empty_positions(world)
        
        if adjacent_positions:
            new_x, new_y = random.choice(adjacent_positions)
            return Planta(new_x, new_y, self.reproduction_age, self.max_age)
        
        return None
    
    def _get_adjacent_empty_positions(self, world) -> List[Tuple[int, int]]:
        """Get list of adjacent empty positions"""
        positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x, new_y = self.x + dx, self.y + dy
                
                if (0 <= new_x < world.width and 
                    0 <= new_y < world.height and 
                    world.grid[new_y][new_x] is None):
                    positions.append((new_x, new_y))
        
        return positions
    
    def should_die(self) -> bool:
        return self.age >= self.max_age
    
    def get_symbol(self) -> str:
        return "*"
    
    def get_colored_symbol(self) -> str:
        return f"{Colors.GREEN}{self.get_symbol()}{Colors.RESET}"

class Herbivoro(Celula):
    def __init__(self, x: int, y: int, brain: CellBrain = None, initial_energy: int = 20, 
                 energy_per_plant: int = 15, reproduction_threshold: int = 30):
        super().__init__(x, y, brain)
        self.energy = initial_energy
        self.energy_per_plant = energy_per_plant
        self.reproduction_threshold = reproduction_threshold
        self._last_energy = initial_energy
    
    def update(self, world) -> Optional['Herbivoro']:
        self.age += 1
        self.energy -= 1
        
        # Update brain fitness with energy changes
        energy_gained = self.energy - self._last_energy
        if energy_gained > 0:
            self.brain.record_energy_gain(energy_gained)
        self._last_energy = self.energy
        
        if self.energy <= 0:
            self.brain.record_death(self.age)
            return None
        
        # Find basic materials for experimentation
        self.find_basic_materials(world)
        
        # Try to discover new things
        self.attempt_discovery(world)
        
        # Use brain to decide movement instead of random
        self._brain_move_and_eat(world)
        
        if self.energy >= self.reproduction_threshold:
            return self._brain_reproduce(world)
        
        return None
    
    def _brain_move_and_eat(self, world):
        """Use brain to decide movement and eating"""
        # Get brain decision
        dx, dy = self.brain.decide_action(self, world)
        
        # Calculate new position
        new_x, new_y = self.x + dx, self.y + dy
        
        # Check bounds
        if not (0 <= new_x < world.width and 0 <= new_y < world.height):
            return  # Can't move outside world
        
        target_cell = world.grid[new_y][new_x]
        
        # If target is a plant, eat it
        if isinstance(target_cell, Planta):
            world.grid[new_y][new_x] = None
            old_energy = self.energy
            self.energy += self.energy_per_plant
            self.brain.record_energy_gain(self.energy - old_energy)
        
        # If target is empty, move there
        if target_cell is None or isinstance(target_cell, Planta):
            world.grid[self.y][self.x] = None
            self.x, self.y = new_x, new_y
            world.grid[self.y][self.x] = self
    
    def _move_and_eat(self, world):
        """Legacy method - kept for compatibility"""
        self._brain_move_and_eat(world)
    
    def _get_adjacent_positions(self, world) -> List[Tuple[int, int]]:
        """Get list of valid adjacent positions (empty or with plants)"""
        positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x, new_y = self.x + dx, self.y + dy
                
                if (0 <= new_x < world.width and 
                    0 <= new_y < world.height):
                    
                    target_cell = world.grid[new_y][new_x]
                    if target_cell is None or isinstance(target_cell, Planta):
                        positions.append((new_x, new_y))
        
        return positions
    
    def _brain_reproduce(self, world) -> Optional['Herbivoro']:
        """Reproduce using brain evolution"""
        adjacent_empty_positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x, new_y = self.x + dx, self.y + dy
                
                if (0 <= new_x < world.width and 
                    0 <= new_y < world.height and 
                    world.grid[new_y][new_x] is None):
                    adjacent_empty_positions.append((new_x, new_y))
        
        if adjacent_empty_positions:
            self.energy //= 2
            new_x, new_y = random.choice(adjacent_empty_positions)
            
            # Create offspring with evolved brain
            child_brain = self.brain.reproduce()
            offspring = Herbivoro(new_x, new_y, child_brain, self.energy // 2, 
                               self.energy_per_plant, self.reproduction_threshold)
            
            return offspring
        
        return None
    
    def _reproduce(self, world) -> Optional['Herbivoro']:
        """Legacy method - kept for compatibility"""
        return self._brain_reproduce(world)
    
    def should_die(self) -> bool:
        return self.energy <= 0
    
    def get_symbol(self) -> str:
        return "O"
    
    def get_colored_symbol(self) -> str:
        return f"{Colors.YELLOW}{self.get_symbol()}{Colors.RESET}"

class Carnivoro(Celula):
    def __init__(self, x: int, y: int, brain: CellBrain = None, initial_energy: int = 30, 
                 energy_per_herbivore: int = 25, reproduction_threshold: int = 50):
        super().__init__(x, y, brain)
        self.energy = initial_energy
        self.energy_per_herbivore = energy_per_herbivore
        self.reproduction_threshold = reproduction_threshold
        self._last_energy = initial_energy
    
    def update(self, world) -> Optional['Carnivoro']:
        self.age += 1
        self.energy -= 2  # Carnivores consume more energy
        
        # Update brain fitness with energy changes
        energy_gained = self.energy - self._last_energy
        if energy_gained > 0:
            self.brain.record_energy_gain(energy_gained)
        self._last_energy = self.energy
        
        if self.energy <= 0:
            self.brain.record_death(self.age)
            return None
        
        # Find basic materials for experimentation  
        self.find_basic_materials(world)
        
        # Try to discover new things (carnivores might discover weapons!)
        self.attempt_discovery(world)
        
        # Use brain for hunting decisions
        self._brain_hunt_and_eat(world)
        
        if self.energy >= self.reproduction_threshold:
            return self._brain_reproduce(world)
        
        return None
    
    def _brain_hunt_and_eat(self, world):
        """Use brain to decide hunting strategy"""
        # Get brain decision
        dx, dy = self.brain.decide_action(self, world)
        
        # Calculate new position
        new_x, new_y = self.x + dx, self.y + dy
        
        # Check bounds
        if not (0 <= new_x < world.width and 0 <= new_y < world.height):
            return  # Can't move outside world
        
        target_cell = world.grid[new_y][new_x]
        
        # If target is a herbivore, hunt it
        if isinstance(target_cell, Herbivoro):
            world.grid[new_y][new_x] = None
            old_energy = self.energy
            self.energy += self.energy_per_herbivore
            self.brain.record_energy_gain(self.energy - old_energy)
        
        # If target is empty, move there
        if target_cell is None or isinstance(target_cell, Herbivoro):
            world.grid[self.y][self.x] = None
            self.x, self.y = new_x, new_y
            world.grid[self.y][self.x] = self
    
    def _hunt_and_eat(self, world):
        """Legacy method - kept for compatibility"""
        self._brain_hunt_and_eat(world)
    
    def _get_adjacent_positions(self, world) -> List[Tuple[int, int]]:
        """Get list of valid adjacent positions (empty or with herbivores)"""
        positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x, new_y = self.x + dx, self.y + dy
                
                if (0 <= new_x < world.width and 
                    0 <= new_y < world.height):
                    
                    target_cell = world.grid[new_y][new_x]
                    if target_cell is None or isinstance(target_cell, Herbivoro):
                        positions.append((new_x, new_y))
        
        return positions
    
    def _brain_reproduce(self, world) -> Optional['Carnivoro']:
        """Reproduce using brain evolution"""
        adjacent_empty_positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                new_x, new_y = self.x + dx, self.y + dy
                
                if (0 <= new_x < world.width and 
                    0 <= new_y < world.height and 
                    world.grid[new_y][new_x] is None):
                    adjacent_empty_positions.append((new_x, new_y))
        
        if adjacent_empty_positions:
            self.energy //= 2
            new_x, new_y = random.choice(adjacent_empty_positions)
            
            # Create offspring with evolved brain
            child_brain = self.brain.reproduce()
            offspring = Carnivoro(new_x, new_y, child_brain, self.energy // 2, 
                               self.energy_per_herbivore, self.reproduction_threshold)
            
            return offspring
        
        return None
    
    def _reproduce(self, world) -> Optional['Carnivoro']:
        """Legacy method - kept for compatibility"""
        return self._brain_reproduce(world)
    
    def should_die(self) -> bool:
        return self.energy <= 0
    
    def get_symbol(self) -> str:
        return "X"
    
    def get_colored_symbol(self) -> str:
        return f"{Colors.RED}{Colors.BOLD}{self.get_symbol()}{Colors.RESET}"