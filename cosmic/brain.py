import random
import math
import numpy as np
from typing import List, Tuple, Optional

class NeuralNetwork:
    """Simple neural network for cell decision making"""
    
    def __init__(self, input_size: int = 10, hidden_size: int = 12, output_size: int = 9, weights: List[float] = None):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Total weights needed: (input->hidden) + hidden_bias + (hidden->output) + output_bias
        self.total_weights = (input_size * hidden_size) + hidden_size + (hidden_size * output_size) + output_size
        
        if weights is None:
            self.weights = [random.uniform(-1, 1) for _ in range(self.total_weights)]
        else:
            self.weights = weights.copy()
    
    def _unpack_weights(self):
        """Unpack flat weights into matrices and biases"""
        idx = 0
        
        # Input to hidden weights
        ih_size = self.input_size * self.hidden_size
        ih_weights = np.array(self.weights[idx:idx + ih_size]).reshape(self.hidden_size, self.input_size)
        idx += ih_size
        
        # Hidden biases
        h_bias = np.array(self.weights[idx:idx + self.hidden_size])
        idx += self.hidden_size
        
        # Hidden to output weights
        ho_size = self.hidden_size * self.output_size
        ho_weights = np.array(self.weights[idx:idx + ho_size]).reshape(self.output_size, self.hidden_size)
        idx += ho_size
        
        # Output biases
        o_bias = np.array(self.weights[idx:idx + self.output_size])
        
        return ih_weights, h_bias, ho_weights, o_bias
    
    def forward(self, inputs: List[float]) -> List[float]:
        """Forward pass through the network"""
        inputs = np.array(inputs)
        ih_weights, h_bias, ho_weights, o_bias = self._unpack_weights()
        
        # Input to hidden layer
        hidden = np.tanh(np.dot(ih_weights, inputs) + h_bias)
        
        # Hidden to output layer
        output = np.tanh(np.dot(ho_weights, hidden) + o_bias)
        
        return output.tolist()
    
    def mutate(self, mutation_rate: float = 0.1, mutation_strength: float = 0.2):
        """Mutate weights with given probability and strength"""
        for i in range(len(self.weights)):
            if random.random() < mutation_rate:
                self.weights[i] += random.uniform(-mutation_strength, mutation_strength)
                # Clamp weights to [-2, 2] range
                self.weights[i] = max(-2.0, min(2.0, self.weights[i]))
    
    def copy(self) -> 'NeuralNetwork':
        """Create a copy of this network"""
        return NeuralNetwork(self.input_size, self.hidden_size, self.output_size, self.weights)

class CellBrain:
    """Brain for cellular decision making with evolutionary capabilities"""
    
    # Vision directions: N, NE, E, SE, S, SW, W, NW
    DIRECTIONS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    
    # Action mapping: 0-7 = move in direction, 8 = stay still
    ACTIONS = DIRECTIONS + [(0, 0)]
    
    def __init__(self, neural_network: NeuralNetwork = None):
        self.network = neural_network if neural_network else NeuralNetwork()
        self.fitness = 0.0  # Fitness score for evolution
        self.age_at_death = 0
        self.energy_gained = 0
        self.offspring_count = 0
    
    def see_environment(self, cell, world) -> List[float]:
        """Generate sensory input from environment (10 values)"""
        vision = self._get_vision(cell, world)  # 8 values
        internal = self._get_internal_state(cell)  # 2 values
        return vision + internal
    
    def _get_vision(self, cell, world) -> List[float]:
        """Get vision in 8 directions around cell"""
        vision = []
        
        for dx, dy in self.DIRECTIONS:
            check_x, check_y = cell.x + dx, cell.y + dy
            
            # Check bounds
            if not (0 <= check_x < world.width and 0 <= check_y < world.height):
                vision.append(-1.0)  # Wall/boundary
                continue
            
            target_cell = world.grid[check_y][check_x]
            
            if target_cell is None:
                vision.append(0.0)  # Empty space
            elif target_cell.__class__.__name__ == 'Planta':
                vision.append(0.5)  # Plant
            elif target_cell.__class__.__name__ == 'Herbivoro':
                vision.append(0.7)  # Herbivore
            elif target_cell.__class__.__name__ == 'Carnivoro':
                vision.append(1.0)  # Carnivore
            else:
                vision.append(0.0)  # Unknown
        
        return vision
    
    def _get_internal_state(self, cell) -> List[float]:
        """Get internal cell state (energy, age)"""
        # Normalize energy (assume max energy around 100)
        energy_normalized = min(1.0, getattr(cell, 'energy', 50) / 100.0) if hasattr(cell, 'energy') else 0.5
        
        # Normalize age (assume max age around 100)
        age_normalized = min(1.0, cell.age / 100.0)
        
        return [energy_normalized, age_normalized]
    
    def decide_action(self, cell, world) -> Tuple[int, int]:
        """Use neural network to decide next action"""
        # Get sensory input
        inputs = self.see_environment(cell, world)
        
        # Get network output
        outputs = self.network.forward(inputs)
        
        # Find action with highest activation
        best_action = outputs.index(max(outputs))
        
        return self.ACTIONS[best_action]
    
    def reproduce(self, partner_brain: Optional['CellBrain'] = None) -> 'CellBrain':
        """Create offspring brain through reproduction"""
        if partner_brain is None:
            # Asexual reproduction - copy and mutate
            child_network = self.network.copy()
            child_network.mutate()
        else:
            # Sexual reproduction - crossover + mutation
            child_network = self._crossover(partner_brain.network)
            child_network.mutate()
        
        child_brain = CellBrain(child_network)
        self.offspring_count += 1
        return child_brain
    
    def _crossover(self, partner_network: NeuralNetwork) -> NeuralNetwork:
        """Create child network through crossover of two parent networks"""
        child_weights = []
        
        for i in range(len(self.network.weights)):
            # Random crossover - take gene from either parent
            if random.random() < 0.5:
                child_weights.append(self.network.weights[i])
            else:
                child_weights.append(partner_network.weights[i])
        
        return NeuralNetwork(weights=child_weights)
    
    def update_fitness(self, cell):
        """Update fitness based on cell performance"""
        base_fitness = cell.age  # Survival time
        
        if hasattr(cell, 'energy'):
            base_fitness += cell.energy * 0.1  # Current energy
            base_fitness += self.energy_gained * 0.05  # Total energy gained
        
        base_fitness += self.offspring_count * 10  # Reproduction bonus
        
        self.fitness = base_fitness
    
    def record_energy_gain(self, amount: float):
        """Record energy gained for fitness calculation"""
        self.energy_gained += amount
    
    def record_death(self, age: int):
        """Record death for fitness calculation"""
        self.age_at_death = age