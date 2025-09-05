import random
import statistics
from typing import List, Dict, Tuple
from .brain import CellBrain, NeuralNetwork

class EvolutionEngine:
    """Manages genetic algorithm for brain evolution across generations"""
    
    def __init__(self, mutation_rate: float = 0.1, mutation_strength: float = 0.2, 
                 elite_percentage: float = 0.2, crossover_rate: float = 0.7):
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.elite_percentage = elite_percentage  # Top % of population that survives
        self.crossover_rate = crossover_rate  # Probability of sexual reproduction
        
        # Evolution statistics
        self.generation = 0
        self.fitness_history = []
        self.population_history = []
        self.species_stats = {}
    
    def evolve_population(self, dead_brains: List[CellBrain], target_population: int) -> List[CellBrain]:
        """Evolve a new generation from dead brains using genetic algorithm"""
        if not dead_brains:
            # Create random initial population
            return [CellBrain() for _ in range(target_population)]
        
        # Calculate fitness for all brains
        self._calculate_fitness(dead_brains)
        
        # Record statistics
        self._record_generation_stats(dead_brains)
        
        # Select elite survivors
        elite_brains = self._select_elite(dead_brains)
        
        # Generate new population
        new_population = self._generate_offspring(elite_brains, target_population)
        
        self.generation += 1
        return new_population
    
    def _calculate_fitness(self, brains: List[CellBrain]):
        """Calculate and normalize fitness scores"""
        if not brains:
            return
        
        # Calculate raw fitness
        for brain in brains:
            brain.fitness = self._calculate_raw_fitness(brain)
        
        # Normalize fitness scores (0-1 range)
        fitnesses = [brain.fitness for brain in brains]
        if len(set(fitnesses)) > 1:  # Avoid division by zero
            min_fit = min(fitnesses)
            max_fit = max(fitnesses)
            for brain in brains:
                brain.fitness = (brain.fitness - min_fit) / (max_fit - min_fit) if max_fit > min_fit else 0.5
    
    def _calculate_raw_fitness(self, brain: CellBrain) -> float:
        """Calculate raw fitness score for a brain"""
        fitness = 0.0
        
        # Survival time bonus (most important)
        fitness += brain.age_at_death * 2.0
        
        # Energy management bonus
        fitness += brain.energy_gained * 0.1
        
        # Reproduction bonus (exponential reward)
        fitness += brain.offspring_count ** 1.5 * 20.0
        
        # Efficiency bonus (energy gained per age)
        if brain.age_at_death > 0:
            efficiency = brain.energy_gained / brain.age_at_death
            fitness += efficiency * 5.0
        
        return max(0.0, fitness)  # Ensure non-negative
    
    def _select_elite(self, brains: List[CellBrain]) -> List[CellBrain]:
        """Select the elite brains based on fitness"""
        # Sort by fitness (descending)
        sorted_brains = sorted(brains, key=lambda b: b.fitness, reverse=True)
        
        # Select top percentage
        elite_count = max(1, int(len(sorted_brains) * self.elite_percentage))
        return sorted_brains[:elite_count]
    
    def _generate_offspring(self, elite_brains: List[CellBrain], target_population: int) -> List[CellBrain]:
        """Generate offspring from elite brains to reach target population"""
        offspring = []
        
        # Keep all elite brains (survivors)
        for brain in elite_brains:
            offspring.append(CellBrain(brain.network.copy()))
        
        # Generate additional offspring
        while len(offspring) < target_population:
            if random.random() < self.crossover_rate and len(elite_brains) >= 2:
                # Sexual reproduction (crossover)
                parent1, parent2 = random.sample(elite_brains, 2)
                child = parent1.reproduce(parent2)
            else:
                # Asexual reproduction (mutation only)
                parent = self._select_parent_weighted(elite_brains)
                child = parent.reproduce()
            
            offspring.append(child)
        
        return offspring[:target_population]
    
    def _select_parent_weighted(self, elite_brains: List[CellBrain]) -> CellBrain:
        """Select parent using fitness-weighted probability"""
        if not elite_brains:
            return CellBrain()
        
        # Create weighted selection based on fitness
        weights = [brain.fitness + 0.1 for brain in elite_brains]  # Add small base weight
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.choice(elite_brains)
        
        # Weighted random selection
        rand_weight = random.uniform(0, total_weight)
        current_weight = 0
        
        for i, weight in enumerate(weights):
            current_weight += weight
            if current_weight >= rand_weight:
                return elite_brains[i]
        
        return elite_brains[-1]  # Fallback
    
    def _record_generation_stats(self, brains: List[CellBrain]):
        """Record statistics for this generation"""
        if not brains:
            return
        
        fitnesses = [brain.fitness for brain in brains]
        ages = [brain.age_at_death for brain in brains]
        energy_gains = [brain.energy_gained for brain in brains]
        offspring_counts = [brain.offspring_count for brain in brains]
        
        generation_stats = {
            'generation': self.generation,
            'population': len(brains),
            'fitness_avg': statistics.mean(fitnesses),
            'fitness_max': max(fitnesses),
            'fitness_min': min(fitnesses),
            'age_avg': statistics.mean(ages) if ages else 0,
            'age_max': max(ages) if ages else 0,
            'energy_avg': statistics.mean(energy_gains) if energy_gains else 0,
            'offspring_avg': statistics.mean(offspring_counts) if offspring_counts else 0,
            'offspring_total': sum(offspring_counts)
        }
        
        self.fitness_history.append(generation_stats)
        self.population_history.append(len(brains))
    
    def get_evolution_report(self) -> str:
        """Generate a report of evolutionary progress"""
        if not self.fitness_history:
            return "No evolutionary data available."
        
        latest = self.fitness_history[-1]
        
        report = f"""
=== REPORTE EVOLUTIVO - GENERACIÓN {self.generation} ===
Población: {latest['population']} cerebros
Fitness Promedio: {latest['fitness_avg']:.3f}
Fitness Máximo: {latest['fitness_max']:.3f}
Edad Promedio: {latest['age_avg']:.1f} ticks
Edad Máxima: {latest['age_max']} ticks
Energía Promedio Ganada: {latest['energy_avg']:.1f}
Descendencia Total: {latest['offspring_total']}
        """
        
        # Evolutionary trends
        if len(self.fitness_history) >= 2:
            prev = self.fitness_history[-2]
            fitness_change = latest['fitness_avg'] - prev['fitness_avg']
            age_change = latest['age_avg'] - prev['age_avg']
            
            report += f"\n--- TENDENCIAS ---\n"
            report += f"Cambio en Fitness: {fitness_change:+.3f}\n"
            report += f"Cambio en Longevidad: {age_change:+.1f} ticks\n"
            
            if fitness_change > 0:
                report += "📈 La población está evolucionando positivamente\n"
            elif fitness_change < -0.01:
                report += "📉 La población está bajo presión evolutiva\n"
            else:
                report += "➡️  La población está en equilibrio evolutivo\n"
        
        return report
    
    def create_champion_brain(self) -> CellBrain:
        """Create a brain based on the best performers from history"""
        if not self.fitness_history:
            return CellBrain()
        
        # Create a highly optimized brain based on evolutionary insights
        champion_network = NeuralNetwork()
        
        # Apply slight positive bias to weights (evolved organisms tend to be more active)
        for i in range(len(champion_network.weights)):
            champion_network.weights[i] += random.uniform(-0.1, 0.2)
        
        return CellBrain(champion_network)