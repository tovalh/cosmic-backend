import random
from typing import List, Optional, Tuple
from .cells import Celula, Planta, Herbivoro, Carnivoro
from .evolution import EvolutionEngine
from .brain import CellBrain

class World:
    def __init__(self, width: int, height: int, evolution_enabled: bool = True):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.tick = 0
        self.step_count = 0  # For cosmic simulation compatibility
        
        # Evolution system
        self.evolution_enabled = evolution_enabled
        self.evolution_engine = EvolutionEngine() if evolution_enabled else None
        self.dead_brains = {'herbivores': [], 'carnivores': []}
        self.generation_length = 500  # Ticks per generation
        
        # Material discovery system
        self.scattered_materials = {}  # (x, y) -> UniverseObject
    
    def add_cell(self, cell: Celula) -> bool:
        """Add cell to world at its position if position is empty"""
        if (0 <= cell.x < self.width and 
            0 <= cell.y < self.height and 
            self.grid[cell.y][cell.x] is None):
            self.grid[cell.y][cell.x] = cell
            return True
        return False
    
    def remove_cell(self, x: int, y: int):
        """Remove cell at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = None
    
    def get_cell(self, x: int, y: int) -> Optional[Celula]:
        """Get cell at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None
    
    def populate_random(self, num_plants: int, num_herbivores: int, num_carnivores: int = 0):
        """Randomly populate world with initial cells"""
        empty_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is None:
                    empty_positions.append((x, y))
        
        total_population = num_plants + num_herbivores + num_carnivores
        if len(empty_positions) < total_population:
            raise ValueError("Not enough empty positions for initial population")
        
        random.shuffle(empty_positions)
        
        # Add plants
        for i in range(num_plants):
            x, y = empty_positions[i]
            plant = Planta(x, y)
            self.grid[y][x] = plant
        
        # Add herbivores
        for i in range(num_plants, num_plants + num_herbivores):
            x, y = empty_positions[i]
            herbivore = Herbivoro(x, y)
            self.grid[y][x] = herbivore
        
        # Add carnivores
        for i in range(num_plants + num_herbivores, total_population):
            x, y = empty_positions[i]
            carnivore = Carnivoro(x, y)
            self.grid[y][x] = carnivore
    
    def update(self):
        """Update all cells in the world for one tick"""
        self.tick += 1
        
        cells_to_update = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    cells_to_update.append(self.grid[y][x])
        
        random.shuffle(cells_to_update)
        
        new_cells = []
        cells_to_remove = []
        
        for cell in cells_to_update:
            if cell not in cells_to_remove:
                new_cell = cell.update(self)
                
                if cell.should_die():
                    cells_to_remove.append(cell)
                    # Collect dead brains for evolution
                    if self.evolution_enabled and hasattr(cell, 'brain'):
                        cell.brain.update_fitness(cell)
                        if isinstance(cell, Herbivoro):
                            self.dead_brains['herbivores'].append(cell.brain)
                        elif isinstance(cell, Carnivoro):
                            self.dead_brains['carnivores'].append(cell.brain)
                
                if new_cell is not None:
                    new_cells.append(new_cell)
        
        for cell in cells_to_remove:
            self.grid[cell.y][cell.x] = None
        
        for new_cell in new_cells:
            if self.grid[new_cell.y][new_cell.x] is None:
                self.grid[new_cell.y][new_cell.x] = new_cell
        
        # Check for generational evolution
        if self.evolution_enabled and self.tick % self.generation_length == 0:
            self._evolve_generation()
    
    def _evolve_generation(self):
        """Evolve a new generation of creatures"""
        if not self.evolution_engine:
            return
        
        # Count current populations
        current_herbivores = 0
        current_carnivores = 0
        
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if isinstance(cell, Herbivoro):
                    current_herbivores += 1
                elif isinstance(cell, Carnivoro):
                    current_carnivores += 1
        
        # Evolve herbivores if we have dead brains
        if self.dead_brains['herbivores']:
            new_herbivore_brains = self.evolution_engine.evolve_population(
                self.dead_brains['herbivores'], max(5, current_herbivores // 4)
            )
            self._spawn_evolved_creatures('herbivore', new_herbivore_brains)
            self.dead_brains['herbivores'] = []
        
        # Evolve carnivores if we have dead brains
        if self.dead_brains['carnivores']:
            new_carnivore_brains = self.evolution_engine.evolve_population(
                self.dead_brains['carnivores'], max(2, current_carnivores // 4)
            )
            self._spawn_evolved_creatures('carnivore', new_carnivore_brains)
            self.dead_brains['carnivores'] = []
    
    def _spawn_evolved_creatures(self, creature_type: str, brains: List[CellBrain]):
        """Spawn evolved creatures in empty locations"""
        empty_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is None:
                    empty_positions.append((x, y))
        
        if not empty_positions:
            return  # No space to spawn
        
        random.shuffle(empty_positions)
        
        for i, brain in enumerate(brains):
            if i >= len(empty_positions):
                break
            
            x, y = empty_positions[i]
            
            if creature_type == 'herbivore':
                creature = Herbivoro(x, y, brain)
            elif creature_type == 'carnivore':
                creature = Carnivoro(x, y, brain)
            else:
                continue
            
            self.grid[y][x] = creature
    
    def get_evolution_report(self) -> str:
        """Get evolution report from evolution engine"""
        if not self.evolution_engine:
            return "Evolution disabled"
        return self.evolution_engine.get_evolution_report()
    
    def get_statistics(self) -> dict:
        """Get population statistics"""
        plant_count = 0
        herbivore_count = 0
        carnivore_count = 0
        total_herbivore_energy = 0
        total_carnivore_energy = 0
        
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if isinstance(cell, Planta):
                    plant_count += 1
                elif isinstance(cell, Herbivoro):
                    herbivore_count += 1
                    total_herbivore_energy += cell.energy
                elif isinstance(cell, Carnivoro):
                    carnivore_count += 1
                    total_carnivore_energy += cell.energy
        
        avg_herbivore_energy = (total_herbivore_energy / herbivore_count 
                               if herbivore_count > 0 else 0)
        avg_carnivore_energy = (total_carnivore_energy / carnivore_count 
                               if carnivore_count > 0 else 0)
        
        total_population = plant_count + herbivore_count + carnivore_count
        
        return {
            'tick': self.tick,
            'plants': plant_count,
            'herbivores': herbivore_count,
            'carnivores': carnivore_count,
            'total_population': total_population,
            'avg_herbivore_energy': avg_herbivore_energy,
            'avg_carnivore_energy': avg_carnivore_energy
        }
    
    def step(self):
        """Single step for cosmic simulation compatibility"""
        self.step_count += 1
        self.update()
    
    def populate(self, plants: int = 50, herbivores: int = 15, carnivores: int = 5):
        """Alias for populate_random for cosmic simulation compatibility"""
        self.populate_random(plants, herbivores, carnivores)
    
    def render(self) -> str:
        """Render world as string for console display"""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell is None:
                    # Check if there's a scattered material here
                    if hasattr(self, 'scattered_materials') and (x, y) in self.scattered_materials:
                        line += "◊"  # Material marker
                    else:
                        line += "."
                else:
                    line += cell.get_colored_symbol()
            lines.append(line)
        return "\n".join(lines)