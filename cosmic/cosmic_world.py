#!/usr/bin/env python3
"""
Cosmic World System - Multi-planetary universe with different environments
Each planet has unique properties, materials, and environmental conditions
"""

import random
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from .world import World
from .objects import UniverseObject
from .properties import PROPERTY_REGISTRY, PropertyType

class PlanetType(Enum):
    """Different types of planets with unique characteristics"""
    TERRAN = "terran"           # Earth-like, balanced ecosystem
    VOLCANIC = "volcanic"       # High heat, mineral rich
    ICE = "ice"                 # Cold, crystalline materials
    GAS_GIANT = "gas_giant"     # Floating islands, energy rich
    DESERT = "desert"           # Dry, sparse resources
    OCEAN = "ocean"             # Water world, organic rich
    CRYSTAL = "crystal"         # Crystalline structures, piezoelectric
    TOXIC = "toxic"             # Dangerous but exotic materials
    MAGNETIC = "magnetic"       # Strong magnetic fields, conductive materials
    QUANTUM = "quantum"         # Exotic physics, strange materials

@dataclass
class CosmicEvent:
    """Events that affect multiple planets"""
    name: str
    description: str
    affected_planets: List[str]
    duration_ticks: int
    effects: Dict[str, Any]
    probability: float = 0.01

@dataclass
class Planet:
    """A planet in the cosmic system"""
    id: str
    name: str
    planet_type: PlanetType
    world: World
    position: Tuple[float, float, float]  # 3D coordinates in space
    native_materials: List[UniverseObject]
    environmental_conditions: Dict[str, float]
    discovery_bonus_multiplier: float = 1.0
    trade_routes: List[str] = None  # IDs of connected planets
    
    def __post_init__(self):
        if self.trade_routes is None:
            self.trade_routes = []

class CosmicSimulation:
    """Manages multiple planets and cosmic events"""
    
    def __init__(self):
        self.planets: Dict[str, Planet] = {}
        self.step_count = 0
        self.active_cosmic_events = []
        self.trade_manifest = {}  # Track objects moving between planets
        self.discovery_network = {}  # Shared discoveries across planets
        
    def create_planet(self, planet_id: str, name: str, planet_type: PlanetType, 
                     size: Tuple[int, int] = (50, 50), position: Tuple[float, float, float] = None) -> Planet:
        """Create a new planet with type-specific characteristics"""
        
        if position is None:
            # Random position in 3D space
            position = (
                random.uniform(-1000, 1000),
                random.uniform(-1000, 1000), 
                random.uniform(-1000, 1000)
            )
        
        # Create the world for this planet
        world = World(size[0], size[1])
        world.step_count = 0
        
        # Generate planet-specific materials and conditions
        native_materials, conditions, discovery_multiplier = self._generate_planet_characteristics(planet_type)
        
        planet = Planet(
            id=planet_id,
            name=name,
            planet_type=planet_type,
            world=world,
            position=position,
            native_materials=native_materials,
            environmental_conditions=conditions,
            discovery_bonus_multiplier=discovery_multiplier
        )
        
        # Seed the planet with native materials scattered around
        self._seed_planet_materials(planet)
        
        self.planets[planet_id] = planet
        return planet
    
    def _generate_planet_characteristics(self, planet_type: PlanetType) -> Tuple[List[UniverseObject], Dict[str, float], float]:
        """Generate materials and conditions specific to planet type"""
        
        materials = []
        conditions = {"temperature": 20.0, "pressure": 1.0, "radiation": 0.0, "magnetic_field": 0.1}
        discovery_multiplier = 1.0
        
        if planet_type == PlanetType.TERRAN:
            materials = [
                UniverseObject("Piedra Terrestre", ["es_duro", "es_pesado"]),
                UniverseObject("Madera Nativa", ["es_organico", "es_fragil", "es_inflamable"]),
                UniverseObject("Agua Pura", ["es_solvente", "es_humedo"]),
                UniverseObject("Mineral de Hierro", ["es_duro", "es_magnetico"]),
                UniverseObject("Planta Medicinal", ["es_organico", "es_curativo"])
            ]
            conditions.update({"temperature": 25.0, "pressure": 1.0, "radiation": 0.1})
        
        elif planet_type == PlanetType.VOLCANIC:
            materials = [
                UniverseObject("Obsidiana", ["es_cortante", "es_fragil", "es_cristalino"]),
                UniverseObject("Azufre Volcánico", ["es_acido", "es_reactivo", "es_explosivo"]),
                UniverseObject("Lava Solidificada", ["es_duro", "retiene_calor", "es_caliente"]),
                UniverseObject("Gas Volcánico", ["es_toxico", "es_caliente", "es_reactivo"]),
                UniverseObject("Cristal de Magma", ["es_cristalino", "es_caliente", "brilla"])
            ]
            conditions.update({"temperature": 80.0, "pressure": 1.5, "radiation": 0.3})
            discovery_multiplier = 1.3  # Heat accelerates reactions
        
        elif planet_type == PlanetType.ICE:
            materials = [
                UniverseObject("Hielo Eterno", ["es_duro", "es_frio", "es_cristalino"]),
                UniverseObject("Cristal de Nitrógeno", ["es_frio", "es_cristalino", "es_fragil"]),
                UniverseObject("Permafrost Orgánico", ["es_organico", "es_frio", "es_preservativo"]),
                UniverseObject("Hielo Metálico", ["es_duro", "es_frio", "conduce_electricidad"]),
                UniverseObject("Vapor Helado", ["es_frio", "es_viscoso", "absorbe_calor"])
            ]
            conditions.update({"temperature": -40.0, "pressure": 0.3, "radiation": 0.05})
            discovery_multiplier = 0.7  # Cold slows reactions
        
        elif planet_type == PlanetType.GAS_GIANT:
            materials = [
                UniverseObject("Gas Noble", ["es_estable", "brilla", "es_liviano"]),
                UniverseObject("Cristal Flotante", ["es_cristalino", "es_liviano", "vibra"]),
                UniverseObject("Plasma Frío", ["brilla", "conduce_electricidad", "genera_campo"]),
                UniverseObject("Núcleo Energético", ["genera_campo", "es_radioactivo", "vibra"]),
                UniverseObject("Éter Condensado", ["es_liviano", "absorbe_luz", "es_viscoso"])
            ]
            conditions.update({"temperature": 15.0, "pressure": 0.1, "radiation": 0.8, "magnetic_field": 2.0})
            discovery_multiplier = 1.5  # High energy environment
        
        elif planet_type == PlanetType.DESERT:
            materials = [
                UniverseObject("Arena Silícea", ["es_abrasivo", "es_cristalino", "absorbe_calor"]),
                UniverseObject("Sal Mineral", ["es_cristalino", "es_solvente", "es_estable"]),
                UniverseObject("Cactus Resistente", ["es_organico", "es_nutritivo", "retiene_agua"]),
                UniverseObject("Piedra Porosa", ["es_liviano", "absorbe_agua", "es_fragil"]),
                UniverseObject("Viento Seco", ["es_abrasivo", "es_caliente", "es_liviano"])
            ]
            conditions.update({"temperature": 50.0, "pressure": 0.8, "radiation": 0.6})
        
        elif planet_type == PlanetType.OCEAN:
            materials = [
                UniverseObject("Agua Salada", ["es_solvente", "conduce_electricidad", "es_humedo"]),
                UniverseObject("Alga Bioluminiscente", ["es_organico", "brilla", "es_nutritivo"]),
                UniverseObject("Concha Nácarada", ["es_duro", "es_cristalino", "es_organico"]),
                UniverseObject("Coral Viviente", ["es_vivo", "es_cristalino", "es_organico"]),
                UniverseObject("Perla Energética", ["brilla", "genera_campo", "es_cristalino"])
            ]
            conditions.update({"temperature": 18.0, "pressure": 2.0, "radiation": 0.2})
            discovery_multiplier = 1.2  # Water accelerates organic reactions
        
        elif planet_type == PlanetType.CRYSTAL:
            materials = [
                UniverseObject("Cuarzo Resonante", ["es_cristalino", "vibra", "es_piezoelectrico"]),
                UniverseObject("Diamante Conductor", ["es_duro", "conduce_electricidad", "es_cristalino"]),
                UniverseObject("Cristal Amplificador", ["es_cristalino", "brilla", "genera_campo"]),
                UniverseObject("Geoda Energética", ["es_cristalino", "genera_campo", "absorbe_luz"]),
                UniverseObject("Prisma Cuántico", ["es_cristalino", "absorbe_luz", "genera_campo"])
            ]
            conditions.update({"temperature": 10.0, "pressure": 1.2, "radiation": 0.4, "magnetic_field": 0.5})
            discovery_multiplier = 1.8  # Crystals amplify energy interactions
        
        elif planet_type == PlanetType.TOXIC:
            materials = [
                UniverseObject("Ácido Alienígena", ["es_acido", "es_toxico", "es_reactivo"]),
                UniverseObject("Esporas Tóxicas", ["es_toxico", "es_organico", "es_venenoso"]),
                UniverseObject("Metal Corrosivo", ["es_duro", "es_toxico", "es_reactivo"]),
                UniverseObject("Gas Mutagénico", ["es_toxico", "es_reactivo", "es_psicoactivo"]),
                UniverseObject("Cristal Venenoso", ["es_cristalino", "es_toxico", "brilla"])
            ]
            conditions.update({"temperature": 35.0, "pressure": 1.3, "radiation": 1.2})
            discovery_multiplier = 2.0  # Extreme conditions create exotic reactions
        
        elif planet_type == PlanetType.MAGNETIC:
            materials = [
                UniverseObject("Hierro Magnético", ["es_magnetico", "es_duro", "conduce_electricidad"]),
                UniverseObject("Superconductor Natural", ["es_superconductor", "conduce_electricidad", "es_frio"]),
                UniverseObject("Campo Cristalizado", ["genera_campo", "es_cristalino", "es_magnetico"]),
                UniverseObject("Bobina Orgánica", ["conduce_electricidad", "es_organico", "es_flexible"]),
                UniverseObject("Plasma Magnético", ["brilla", "es_magnetico", "genera_campo"])
            ]
            conditions.update({"magnetic_field": 5.0, "radiation": 0.8})
            discovery_multiplier = 1.6  # Magnetic fields enhance electrical discoveries
        
        elif planet_type == PlanetType.QUANTUM:
            materials = [
                UniverseObject("Materia Oscura Simulada", ["absorbe_luz", "genera_campo", "es_frio"]),
                UniverseObject("Partícula Entrelazada", ["genera_campo", "vibra", "es_liviano"]),
                UniverseObject("Vacío Cristalizado", ["es_cristalino", "absorbe_luz", "genera_campo"]),
                UniverseObject("Energía Pura", ["brilla", "genera_campo", "es_liviano"]),
                UniverseObject("Anomalía Temporal", ["vibra", "genera_campo", "absorbe_luz"])
            ]
            conditions.update({"radiation": 2.0, "magnetic_field": 3.0, "pressure": 0.05})
            discovery_multiplier = 3.0  # Quantum effects create breakthrough discoveries
        
        return materials, conditions, discovery_multiplier
    
    def _seed_planet_materials(self, planet: Planet):
        """Scatter native materials across the planet surface"""
        world = planet.world
        materials_per_spawn = 3  # How many materials to place
        
        for _ in range(materials_per_spawn * len(planet.native_materials)):
            x = random.randint(0, world.width - 1)
            y = random.randint(0, world.height - 1)
            
            # Only place materials in empty spaces
            if world.grid[y][x] is None:
                material = random.choice(planet.native_materials)
                # Materials don't occupy grid spaces but can be found by cells
                if not hasattr(world, 'scattered_materials'):
                    world.scattered_materials = {}
                world.scattered_materials[(x, y)] = material
    
    def step_all_planets(self):
        """Advance simulation on all planets simultaneously"""
        self.step_count += 1
        
        discoveries_this_step = []
        
        # Step each planet
        for planet in self.planets.values():
            planet.world.step_count = self.step_count
            planet.world.step()
            
            # Check for new discoveries on this planet
            planet_discoveries = self._check_planet_discoveries(planet)
            discoveries_this_step.extend(planet_discoveries)
        
        # Process cosmic events
        self._process_cosmic_events()
        
        # Handle inter-planetary trade and communication
        self._process_interplanetary_interactions()
        
        # Share breakthrough discoveries across planets
        self._share_cosmic_knowledge(discoveries_this_step)
        
        return discoveries_this_step
    
    def _check_planet_discoveries(self, planet: Planet) -> List[Any]:
        """Check for new discoveries on a specific planet"""
        # This would integrate with the discovery system
        # For now, return empty list
        return []
    
    def _process_cosmic_events(self):
        """Process active cosmic events and spawn new ones"""
        # Remove expired events
        self.active_cosmic_events = [
            event for event in self.active_cosmic_events 
            if event.duration_ticks > 0
        ]
        
        # Decrease duration on active events
        for event in self.active_cosmic_events:
            event.duration_ticks -= 1
        
        # Chance to spawn new cosmic event
        if random.random() < 0.01:  # 1% chance per step
            self._spawn_cosmic_event()
    
    def _spawn_cosmic_event(self):
        """Spawn a random cosmic event"""
        events = [
            CosmicEvent(
                name="Tormenta Solar",
                description="Radiación intensa afecta materiales electromagnéticos",
                affected_planets=random.sample(list(self.planets.keys()), 
                                             min(3, len(self.planets))),
                duration_ticks=50,
                effects={"radiation_boost": 2.0, "magnetic_interference": 1.5}
            ),
            CosmicEvent(
                name="Alineación Cuántica",
                description="Efectos cuánticos intensificados en múltiples mundos",
                affected_planets=list(self.planets.keys()),
                duration_ticks=20,
                effects={"discovery_multiplier": 2.5, "exotic_materials": True}
            ),
            CosmicEvent(
                name="Lluvia de Meteoritos",
                description="Nuevos materiales extraterrestres llegan",
                affected_planets=random.sample(list(self.planets.keys()), 
                                             min(2, len(self.planets))),
                duration_ticks=30,
                effects={"new_materials": True, "impact_damage": 0.1}
            )
        ]
        
        if self.planets:
            event = random.choice(events)
            self.active_cosmic_events.append(event)
            print(f"🌌 EVENTO CÓSMICO: {event.name} - {event.description}")
    
    def _process_interplanetary_interactions(self):
        """Handle trade and communication between planets"""
        # Calculate distances and establish trade routes
        planet_ids = list(self.planets.keys())
        
        for i, planet1_id in enumerate(planet_ids):
            for planet2_id in planet_ids[i+1:]:
                distance = self._calculate_distance(planet1_id, planet2_id)
                
                # Establish trade routes for nearby planets
                if distance < 500 and random.random() < 0.05:  # 5% chance
                    planet1 = self.planets[planet1_id]
                    planet2 = self.planets[planet2_id]
                    
                    if planet2_id not in planet1.trade_routes:
                        planet1.trade_routes.append(planet2_id)
                    if planet1_id not in planet2.trade_routes:
                        planet2.trade_routes.append(planet1_id)
                        
                    print(f"🚀 Nueva ruta comercial: {planet1.name} ↔ {planet2.name}")
    
    def _calculate_distance(self, planet1_id: str, planet2_id: str) -> float:
        """Calculate 3D distance between two planets"""
        p1_pos = self.planets[planet1_id].position
        p2_pos = self.planets[planet2_id].position
        
        return np.sqrt(
            (p1_pos[0] - p2_pos[0])**2 + 
            (p1_pos[1] - p2_pos[1])**2 + 
            (p1_pos[2] - p2_pos[2])**2
        )
    
    def _share_cosmic_knowledge(self, discoveries: List[Any]):
        """Share breakthrough discoveries across connected planets"""
        for discovery in discoveries:
            # Major discoveries spread across trade networks
            if hasattr(discovery, 'significance') and discovery.significance > 15:
                print(f"🌍 DESCUBRIMIENTO CÓSMICO COMPARTIDO: {discovery.name}")
                # Implementation would spread discovery to connected planets
    
    def get_cosmic_status(self) -> str:
        """Get status report of the cosmic simulation"""
        report = f"🌌 ESTADO CÓSMICO - Tick {self.step_count}\n"
        report += "=" * 50 + "\n"
        
        # Planet status
        for planet in self.planets.values():
            cell_count = sum(1 for row in planet.world.grid for cell in row if cell is not None)
            report += f"🪐 {planet.name} ({planet.planet_type.value}): {cell_count} células\n"
            report += f"   Temperatura: {planet.environmental_conditions['temperature']:.1f}°C\n"
            report += f"   Rutas comerciales: {len(planet.trade_routes)}\n"
        
        # Active events
        if self.active_cosmic_events:
            report += "\n⚡ EVENTOS ACTIVOS:\n"
            for event in self.active_cosmic_events:
                report += f"   • {event.name} ({event.duration_ticks} ticks restantes)\n"
        
        return report
    
    def populate_planet(self, planet_id: str, plants: int = 50, herbivores: int = 15, carnivores: int = 5):
        """Populate a planet with initial life forms"""
        if planet_id not in self.planets:
            return False
        
        world = self.planets[planet_id].world
        world.populate(plants, herbivores, carnivores)
        return True

# Example usage and testing functions
def create_example_solar_system() -> CosmicSimulation:
    """Create an example multi-planetary system"""
    cosmic_sim = CosmicSimulation()
    
    # Create diverse planets
    cosmic_sim.create_planet("terra", "Nueva Tierra", PlanetType.TERRAN, (60, 40))
    cosmic_sim.create_planet("vulkan", "Mundo Volcánico", PlanetType.VOLCANIC, (50, 50))
    cosmic_sim.create_planet("frost", "Planeta Helado", PlanetType.ICE, (45, 45))
    cosmic_sim.create_planet("crystal", "Reino Cristalino", PlanetType.CRYSTAL, (40, 60))
    cosmic_sim.create_planet("quantum", "Mundo Cuántico", PlanetType.QUANTUM, (35, 35))
    
    # Populate planets
    cosmic_sim.populate_planet("terra", plants=100, herbivores=30, carnivores=10)
    cosmic_sim.populate_planet("vulkan", plants=20, herbivores=10, carnivores=8)
    cosmic_sim.populate_planet("frost", plants=30, herbivores=15, carnivores=5)
    cosmic_sim.populate_planet("crystal", plants=40, herbivores=20, carnivores=6)
    cosmic_sim.populate_planet("quantum", plants=15, herbivores=8, carnivores=3)
    
    return cosmic_sim

if __name__ == "__main__":
    # Test the cosmic simulation
    print("🌌 INICIANDO SIMULACIÓN CÓSMICA")
    cosmic = create_example_solar_system()
    
    print(cosmic.get_cosmic_status())
    
    # Run a few steps
    for i in range(10):
        print(f"\n--- TICK {i+1} ---")
        discoveries = cosmic.step_all_planets()
        
        if i % 5 == 4:  # Every 5 steps, show status
            print(cosmic.get_cosmic_status())