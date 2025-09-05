from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import uuid
from .properties import PropertyValue, PropertyType, PROPERTY_REGISTRY
import random

@dataclass
class ObjectState:
    """Represents the current state of an object"""
    durability: int = 100  # 0 = destroyed
    temperature: float = 20.0  # Celsius
    mass: float = 1.0  # Relative mass
    energy_level: float = 0.0  # Internal energy
    is_active: bool = True

class UniverseObject:
    """Base class for all objects in the universe that can have properties and interact"""
    
    def __init__(self, name: str, base_properties: List[str] = None, x: int = 0, y: int = 0):
        self.id = str(uuid.uuid4())
        self.name = name
        self.x = x
        self.y = y
        self.properties = {}  # Dict of property_name -> PropertyValue
        self.state = ObjectState()
        self.history = []  # History of interactions and changes
        self.age = 0
        
        # Initialize with base properties
        if base_properties:
            for prop_name in base_properties:
                self.add_property(prop_name)
    
    def add_property(self, property_name: str, intensity: float = None) -> bool:
        """Add a property to this object"""
        prop_instance = PROPERTY_REGISTRY.create_property_instance(property_name, intensity)
        if prop_instance:
            self.properties[property_name] = prop_instance
            self._log_change(f"Gained property: {prop_instance}")
            return True
        return False
    
    def remove_property(self, property_name: str) -> bool:
        """Remove a property from this object (if it's not permanent)"""
        if property_name in self.properties:
            prop = self.properties[property_name]
            if not prop.is_permanent:
                del self.properties[property_name]
                self._log_change(f"Lost property: {prop.name}")
                return True
            else:
                self._log_change(f"Cannot remove permanent property: {prop.name}")
        return False
    
    def has_property(self, property_name: str) -> bool:
        """Check if object has a specific property"""
        return property_name in self.properties
    
    def get_property(self, property_name: str) -> Optional[PropertyValue]:
        """Get a specific property"""
        return self.properties.get(property_name)
    
    def get_properties_by_type(self, prop_type: PropertyType) -> List[PropertyValue]:
        """Get all properties of a specific type"""
        return [prop for prop in self.properties.values() if prop.property_type == prop_type]
    
    def modify_property_intensity(self, property_name: str, delta: float) -> bool:
        """Modify the intensity of a property"""
        if property_name in self.properties:
            prop = self.properties[property_name]
            old_intensity = prop.intensity
            prop.intensity = max(0.0, min(1.0, prop.intensity + delta))
            
            # Remove property if intensity reaches 0
            if prop.intensity <= 0.0 and not prop.is_permanent:
                self.remove_property(property_name)
            else:
                self._log_change(f"Property {property_name} intensity: {old_intensity:.2f} -> {prop.intensity:.2f}")
            return True
        return False
    
    def take_damage(self, amount: int) -> bool:
        """Apply damage to the object"""
        old_durability = self.state.durability
        self.state.durability = max(0, self.state.durability - amount)
        
        self._log_change(f"Took {amount} damage: {old_durability} -> {self.state.durability}")
        
        # Check if object is destroyed
        if self.state.durability <= 0:
            self.state.is_active = False
            self._log_change("Object destroyed!")
            return True  # Object is destroyed
        
        # Lose fragile properties when badly damaged
        if self.state.durability < 30 and self.has_property("es_fragil"):
            self.add_property("esta_roto")
        
        return False
    
    def heal(self, amount: int):
        """Restore durability to the object"""
        old_durability = self.state.durability
        self.state.durability = min(100, self.state.durability + amount)
        self._log_change(f"Healed {amount}: {old_durability} -> {self.state.durability}")
    
    def change_temperature(self, delta_temp: float):
        """Change object temperature"""
        old_temp = self.state.temperature
        self.state.temperature += delta_temp
        
        # Temperature affects properties
        if self.state.temperature > 100 and self.has_property("es_organico"):
            self.add_property("esta_quemado")
        elif self.state.temperature < 0 and self.has_property("es_humedo"):
            self.remove_property("es_humedo")  # Water freezes
        
        self._log_change(f"Temperature change: {old_temp:.1f}°C -> {self.state.temperature:.1f}°C")
    
    def combine_with(self, other_object: 'UniverseObject', action: str = "combine") -> 'CombinationResult':
        """Attempt to combine this object with another"""
        from .interactions import InteractionEngine  # Import here to avoid circular imports
        engine = InteractionEngine()
        return engine.interact(self, other_object, action)
    
    def get_interaction_strength(self) -> float:
        """Calculate how strong this object is in interactions"""
        strength = 0.0
        
        # Physical strength
        if self.has_property("es_duro"):
            strength += self.get_property("es_duro").intensity * 10
        if self.has_property("es_cortante"):
            strength += self.get_property("es_cortante").intensity * 15
        if self.has_property("es_puntiagudo"):
            strength += self.get_property("es_puntiagudo").intensity * 12
        
        # State modifiers
        strength *= (self.state.durability / 100.0)  # Damaged objects are weaker
        
        return strength
    
    def update(self):
        """Update object state each tick"""
        self.age += 1
        
        # Natural decay for temporary properties
        temp_properties = [name for name, prop in self.properties.items() 
                          if not prop.is_permanent and random.random() < 0.01]  # 1% chance per tick
        
        for prop_name in temp_properties:
            if random.random() < 0.1:  # 10% chance to decay
                self.modify_property_intensity(prop_name, -0.1)
        
        # Temperature normalization (slowly return to room temperature)
        if self.state.temperature != 20.0:
            temp_diff = 20.0 - self.state.temperature
            self.state.temperature += temp_diff * 0.01  # 1% normalization per tick
    
    def _log_change(self, description: str):
        """Log a change to this object's history"""
        self.history.append({
            'tick': self.age,
            'description': description,
            'state_snapshot': {
                'durability': self.state.durability,
                'temperature': self.state.temperature,
                'properties': list(self.properties.keys())
            }
        })
        
        # Keep only last 50 history entries
        if len(self.history) > 50:
            self.history = self.history[-50:]
    
    def get_status_report(self) -> str:
        """Get a detailed status report of this object"""
        report = f"=== {self.name} (ID: {self.id[:8]}) ===\n"
        report += f"Position: ({self.x}, {self.y})\n"
        report += f"Age: {self.age} ticks\n"
        report += f"Durability: {self.state.durability}/100\n"
        report += f"Temperature: {self.state.temperature:.1f}°C\n"
        report += f"Mass: {self.state.mass:.1f}\n"
        report += f"Active: {self.state.is_active}\n"
        
        if self.properties:
            report += "\nProperties:\n"
            for prop_name, prop in self.properties.items():
                report += f"  - {prop}\n"
        
        if self.history:
            report += f"\nRecent History (last {min(5, len(self.history))} events):\n"
            for event in self.history[-5:]:
                report += f"  Tick {event['tick']}: {event['description']}\n"
        
        return report
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'properties': {name: {
                'name': prop.name,
                'type': prop.property_type.value,
                'intensity': prop.intensity,
                'is_permanent': prop.is_permanent
            } for name, prop in self.properties.items()},
            'state': {
                'durability': self.state.durability,
                'temperature': self.state.temperature,
                'mass': self.state.mass,
                'energy_level': self.state.energy_level,
                'is_active': self.state.is_active
            },
            'age': self.age
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniverseObject':
        """Deserialize object from dictionary"""
        obj = cls(data['name'], [], data.get('x', 0), data.get('y', 0))
        obj.id = data['id']
        obj.age = data.get('age', 0)
        
        # Restore state
        state_data = data.get('state', {})
        obj.state.durability = state_data.get('durability', 100)
        obj.state.temperature = state_data.get('temperature', 20.0)
        obj.state.mass = state_data.get('mass', 1.0)
        obj.state.energy_level = state_data.get('energy_level', 0.0)
        obj.state.is_active = state_data.get('is_active', True)
        
        # Restore properties
        for prop_name, prop_data in data.get('properties', {}).items():
            obj.add_property(prop_name, prop_data['intensity'])
        
        return obj
    
    def __str__(self):
        props_str = ", ".join([str(prop) for prop in self.properties.values()])
        return f"{self.name}[{props_str}]"
    
    def __repr__(self):
        return f"UniverseObject('{self.name}', {list(self.properties.keys())})"

class CombinationResult:
    """Result of combining/interacting two objects"""
    
    def __init__(self, success: bool = False):
        self.success = success
        self.new_objects = []  # List of newly created objects
        self.modified_objects = []  # List of objects that were modified
        self.destroyed_objects = []  # List of objects that were destroyed
        self.description = ""
        self.significance_score = 0.0  # How significant was this interaction?
        self.new_concepts_discovered = []  # Any new concepts that emerged
    
    def add_new_object(self, obj: UniverseObject):
        """Add a newly created object to the result"""
        self.new_objects.append(obj)
    
    def add_modified_object(self, obj: UniverseObject):
        """Add a modified object to the result"""
        if obj not in self.modified_objects:
            self.modified_objects.append(obj)
    
    def add_destroyed_object(self, obj: UniverseObject):
        """Add a destroyed object to the result"""
        self.destroyed_objects.append(obj)
    
    def calculate_significance(self) -> float:
        """Calculate how significant this interaction was"""
        score = 0.0
        
        # New objects are highly significant
        score += len(self.new_objects) * 10.0
        
        # New properties discovered
        for obj in self.modified_objects:
            score += len([prop for prop in obj.properties.values() 
                         if prop.property_type == PropertyType.STATE]) * 2.0
        
        # Destruction is significant
        score += len(self.destroyed_objects) * 5.0
        
        self.significance_score = score
        return score
    
    def get_summary(self) -> str:
        """Get a summary of what happened"""
        if not self.success:
            return "Interaction failed or had no effect"
        
        summary = self.description + "\n"
        
        if self.new_objects:
            summary += f"Created: {', '.join([obj.name for obj in self.new_objects])}\n"
        
        if self.modified_objects:
            summary += f"Modified: {', '.join([obj.name for obj in self.modified_objects])}\n"
        
        if self.destroyed_objects:
            summary += f"Destroyed: {', '.join([obj.name for obj in self.destroyed_objects])}\n"
        
        summary += f"Significance: {self.significance_score:.1f}"
        
        return summary

# Common object templates
def create_basic_objects():
    """Create some basic objects for testing"""
    
    # Basic materials
    rock = UniverseObject("Piedra", ["es_duro", "es_pesado"])
    stick = UniverseObject("Palo", ["es_fragil", "es_organico", "es_liviano"])
    water = UniverseObject("Agua", ["es_humedo", "es_frio"])
    fire = UniverseObject("Fuego", ["es_caliente", "brilla"])
    
    # Tools
    sharp_rock = UniverseObject("Piedra Afilada", ["es_duro", "es_cortante", "es_pesado"])
    
    # Biological
    plant = UniverseObject("Planta", ["es_organico", "es_fragil", "es_nutritivo"])
    mushroom = UniverseObject("Hongo", ["es_organico", "es_venenoso"])
    
    return [rock, stick, water, fire, sharp_rock, plant, mushroom]