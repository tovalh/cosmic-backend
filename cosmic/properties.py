from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random

class PropertyType(Enum):
    """Types of properties that define how they behave"""
    PHYSICAL = "physical"      # Material properties (es_duro, es_fragil)
    THERMAL = "thermal"        # Temperature related (es_caliente, es_frio)
    CHEMICAL = "chemical"      # Chemical properties (es_acido, es_alcalino)
    BIOLOGICAL = "biological"  # Living properties (es_organico, es_venenoso)
    ENERGY = "energy"          # Energy related (conduce_electricidad, es_magnetico)
    STATE = "state"            # Temporary states (esta_mojado, esta_quemado)

@dataclass
class PropertyValue:
    """Represents a property with its intensity/value"""
    name: str
    property_type: PropertyType
    intensity: float = 1.0  # How strong is this property (0.0 - 1.0)
    is_permanent: bool = True  # Can this property be lost?
    description: str = ""
    
    def __str__(self):
        return f"{self.name}({self.intensity:.2f})"

class Property:
    """Base class for all properties in the universe"""
    
    def __init__(self, name: str, property_type: PropertyType, intensity: float = 1.0, 
                 is_permanent: bool = True, description: str = ""):
        self.name = name
        self.property_type = property_type
        self.intensity = intensity
        self.is_permanent = is_permanent
        self.description = description
        self.interactions = {}  # Dict of property_name -> interaction_function
    
    def add_interaction(self, other_property: str, interaction_func: Callable):
        """Add an interaction rule with another property"""
        self.interactions[other_property] = interaction_func
    
    def interact_with(self, other_property: 'Property', context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Define what happens when this property interacts with another"""
        if context is None:
            context = {}
        
        # Check if we have a specific interaction rule
        if other_property.name in self.interactions:
            return self.interactions[other_property.name](self, other_property, context)
        
        # Default interaction based on property types
        return self._default_interaction(other_property, context)
    
    def _default_interaction(self, other_property: 'Property', context: Dict[str, Any]) -> Dict[str, Any]:
        """Default interaction rules based on property types"""
        result = {
            'success': False,
            'damage': 0,
            'new_properties': [],
            'lost_properties': [],
            'description': f"{self.name} has no specific interaction with {other_property.name}"
        }
        
        # Physical interactions
        if self.property_type == PropertyType.PHYSICAL:
            if self.name == "es_duro" and other_property.name == "es_fragil":
                result.update({
                    'success': True,
                    'damage': int(self.intensity * 10),
                    'lost_properties': [other_property.name] if other_property.intensity < self.intensity else [],
                    'description': f"Hard object damages fragile material"
                })
            elif self.name == "es_cortante" and other_property.name == "es_fragil":
                result.update({
                    'success': True,
                    'new_properties': [PropertyValue("es_puntiagudo", PropertyType.PHYSICAL, 0.8, False)],
                    'description': f"Sharp object creates pointed version of fragile material"
                })
        
        # Thermal interactions
        elif self.property_type == PropertyType.THERMAL:
            if self.name == "es_caliente" and other_property.name == "es_organico":
                result.update({
                    'success': True,
                    'damage': int(self.intensity * 20),
                    'new_properties': [PropertyValue("esta_quemado", PropertyType.STATE, 1.0, False)],
                    'description': f"Heat burns organic material"
                })
            elif self.name == "es_caliente" and other_property.name == "es_humedo":
                result.update({
                    'success': True,
                    'lost_properties': ["es_humedo"],
                    'description': f"Heat evaporates moisture"
                })
        
        # Chemical interactions
        elif self.property_type == PropertyType.CHEMICAL:
            if self.name == "es_acido" and other_property.property_type == PropertyType.PHYSICAL:
                result.update({
                    'success': True,
                    'damage': int(self.intensity * 15),
                    'description': f"Acid corrodes material"
                })
        
        return result
    
    def copy(self) -> 'Property':
        """Create a copy of this property"""
        new_prop = Property(self.name, self.property_type, self.intensity, 
                           self.is_permanent, self.description)
        new_prop.interactions = self.interactions.copy()
        return new_prop
    
    def __str__(self):
        return f"{self.name}({self.intensity:.2f})"
    
    def __repr__(self):
        return f"Property('{self.name}', {self.property_type}, {self.intensity})"

class PropertyRegistry:
    """Global registry of all known properties"""
    
    def __init__(self):
        self.properties = {}
        self._initialize_basic_properties()
    
    def _initialize_basic_properties(self):
        """Initialize fundamental properties of the universe"""
        
        # Physical properties
        self.register_property("es_duro", PropertyType.PHYSICAL, "Resistant to breaking")
        self.register_property("es_fragil", PropertyType.PHYSICAL, "Easily broken or damaged")
        self.register_property("es_cortante", PropertyType.PHYSICAL, "Can cut other materials")
        self.register_property("es_puntiagudo", PropertyType.PHYSICAL, "Has a sharp point")
        self.register_property("es_pesado", PropertyType.PHYSICAL, "Has significant mass")
        self.register_property("es_liviano", PropertyType.PHYSICAL, "Has little mass")
        self.register_property("es_flexible", PropertyType.PHYSICAL, "Can bend without breaking")
        self.register_property("es_elastico", PropertyType.PHYSICAL, "Returns to original shape")
        self.register_property("es_viscoso", PropertyType.PHYSICAL, "Thick, sticky consistency")
        self.register_property("es_cristalino", PropertyType.PHYSICAL, "Has ordered crystalline structure")
        
        # Thermal properties
        self.register_property("es_caliente", PropertyType.THERMAL, "Generates or retains heat")
        self.register_property("es_frio", PropertyType.THERMAL, "Absorbs heat or is cold")
        self.register_property("es_inflamable", PropertyType.THERMAL, "Can catch fire")
        self.register_property("retiene_calor", PropertyType.THERMAL, "Stores thermal energy well")
        self.register_property("conduce_calor", PropertyType.THERMAL, "Transfers heat efficiently")
        self.register_property("es_incombustible", PropertyType.THERMAL, "Cannot be burned")
        
        # Chemical properties
        self.register_property("es_acido", PropertyType.CHEMICAL, "Corrosive acidic substance")
        self.register_property("es_alcalino", PropertyType.CHEMICAL, "Basic/alkaline substance")
        self.register_property("es_toxico", PropertyType.CHEMICAL, "Harmful to living things")
        self.register_property("es_reactivo", PropertyType.CHEMICAL, "Reacts easily with other substances")
        self.register_property("es_estable", PropertyType.CHEMICAL, "Resists chemical change")
        self.register_property("es_catalizador", PropertyType.CHEMICAL, "Accelerates chemical reactions")
        self.register_property("es_explosivo", PropertyType.CHEMICAL, "Can explode under conditions")
        self.register_property("es_solvente", PropertyType.CHEMICAL, "Dissolves other substances")
        
        # Biological properties
        self.register_property("es_organico", PropertyType.BIOLOGICAL, "Made of living/once-living matter")
        self.register_property("es_vivo", PropertyType.BIOLOGICAL, "Currently alive and active")
        self.register_property("es_nutritivo", PropertyType.BIOLOGICAL, "Provides nourishment")
        self.register_property("es_venenoso", PropertyType.BIOLOGICAL, "Toxic when consumed")
        self.register_property("es_curativo", PropertyType.BIOLOGICAL, "Has healing properties")
        self.register_property("es_regenerativo", PropertyType.BIOLOGICAL, "Can regrow or repair itself")
        self.register_property("es_fermentable", PropertyType.BIOLOGICAL, "Can undergo fermentation")
        self.register_property("es_psicoactivo", PropertyType.BIOLOGICAL, "Affects consciousness or perception")
        
        # Energy properties
        self.register_property("conduce_electricidad", PropertyType.ENERGY, "Allows electricity to flow")
        self.register_property("es_magnetico", PropertyType.ENERGY, "Has magnetic properties")
        self.register_property("brilla", PropertyType.ENERGY, "Emits light")
        self.register_property("absorbe_luz", PropertyType.ENERGY, "Absorbs light energy")
        self.register_property("es_radioactivo", PropertyType.ENERGY, "Emits radiation")
        self.register_property("vibra", PropertyType.ENERGY, "Produces vibrations or sound")
        self.register_property("es_superconductor", PropertyType.ENERGY, "Conducts with zero resistance")
        self.register_property("genera_campo", PropertyType.ENERGY, "Creates an energy field")
        self.register_property("es_piezoelectrico", PropertyType.ENERGY, "Generates electricity under pressure")
        
        # State properties (temporary)
        self.register_property("es_humedo", PropertyType.STATE, "Contains moisture", is_permanent=False)
        self.register_property("esta_mojado", PropertyType.STATE, "Covered with liquid", is_permanent=False)
        self.register_property("esta_quemado", PropertyType.STATE, "Has been burned", is_permanent=False)
        self.register_property("esta_roto", PropertyType.STATE, "Is damaged or broken", is_permanent=False)
        self.register_property("esta_cargado", PropertyType.STATE, "Has electrical charge", is_permanent=False)
        self.register_property("esta_magnetizado", PropertyType.STATE, "Is temporarily magnetized", is_permanent=False)
        self.register_property("esta_activado", PropertyType.STATE, "Is in an active/energized state", is_permanent=False)
        self.register_property("esta_concentrado", PropertyType.STATE, "Is in concentrated form", is_permanent=False)
        self.register_property("esta_purificado", PropertyType.STATE, "Has been refined/purified", is_permanent=False)
        self.register_property("es_hibrido", PropertyType.STATE, "Is a combination of different materials", is_permanent=False)
    
    def register_property(self, name: str, prop_type: PropertyType, description: str, 
                         intensity: float = 1.0, is_permanent: bool = True) -> Property:
        """Register a new property in the universe"""
        prop = Property(name, prop_type, intensity, is_permanent, description)
        self.properties[name] = prop
        return prop
    
    def get_property(self, name: str) -> Optional[Property]:
        """Get a property by name"""
        return self.properties.get(name)
    
    def get_properties_by_type(self, prop_type: PropertyType) -> List[Property]:
        """Get all properties of a specific type"""
        return [prop for prop in self.properties.values() if prop.property_type == prop_type]
    
    def create_property_instance(self, name: str, intensity: float = None) -> Optional[PropertyValue]:
        """Create an instance of a property with optional custom intensity"""
        template = self.get_property(name)
        if not template:
            return None
        
        actual_intensity = intensity if intensity is not None else template.intensity
        return PropertyValue(
            name=template.name,
            property_type=template.property_type,
            intensity=actual_intensity,
            is_permanent=template.is_permanent,
            description=template.description
        )
    
    def list_all_properties(self) -> Dict[str, Property]:
        """Get all registered properties"""
        return self.properties.copy()

# Global property registry
PROPERTY_REGISTRY = PropertyRegistry()