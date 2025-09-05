from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from .objects import UniverseObject, CombinationResult
from .interactions import InteractionType

class DiscoveryType(Enum):
    """Types of discoveries that can be made"""
    NEW_OBJECT = "new_object"                    # A completely new type of object
    NEW_PROPERTY = "new_property"                # A new property emerges
    TOOL_CREATION = "tool_creation"              # A functional tool is made
    COMPOUND_CREATION = "compound_creation"      # Mixing creates new compound
    PROCESS_DISCOVERY = "process_discovery"      # A useful process is found
    PROPERTY_COMBINATION = "property_combination" # New property combinations
    BREAKTHROUGH = "breakthrough"                # Major significant discovery

@dataclass
class Discovery:
    """Represents a significant discovery in the universe"""
    id: str
    discovery_type: DiscoveryType
    name: str
    description: str
    significance: float
    objects_involved: List[str] = field(default_factory=list)
    properties_involved: List[str] = field(default_factory=list)
    interaction_sequence: List[str] = field(default_factory=list)
    timestamp: int = 0
    discoverer_id: Optional[str] = None  # Which cell/entity made this discovery
    reproducible: bool = False           # Can this be reproduced reliably?
    applications: List[str] = field(default_factory=list)  # What uses has this been put to?

class DiscoveryDetector:
    """Detects when significant discoveries are made"""
    
    def __init__(self, significance_threshold: float = 5.0):
        self.significance_threshold = significance_threshold
        self.discoveries = {}  # Dict[str, Discovery]
        self.object_patterns = {}  # Track what objects are created from what
        self.property_emergence = {}  # Track when new properties appear
        self.interaction_chains = []  # Track sequences of interactions
        self.next_discovery_id = 1
    
    def analyze_interaction_result(self, result: CombinationResult, 
                                 tick: int = 0, discoverer_id: str = None) -> Optional[Discovery]:
        """Analyze a result to see if it represents a significant discovery"""
        
        if not result.success or result.significance_score < self.significance_threshold:
            return None
        
        discovery = None
        
        # Check for new object creation
        if result.new_objects:
            discovery = self._detect_new_object_discovery(result, tick, discoverer_id)
        
        # Check for new property combinations
        elif result.modified_objects:
            discovery = self._detect_property_discovery(result, tick, discoverer_id)
        
        # Check for tool creation patterns
        if discovery is None and self._is_tool_creation(result):
            discovery = self._detect_tool_discovery(result, tick, discoverer_id)
        
        if discovery:
            self.discoveries[discovery.id] = discovery
            self._update_knowledge_base(discovery, result)
        
        return discovery
    
    def _detect_new_object_discovery(self, result: CombinationResult, 
                                   tick: int, discoverer_id: str) -> Optional[Discovery]:
        """Detect when a truly new type of object is created"""
        
        for new_obj in result.new_objects:
            object_signature = self._get_object_signature(new_obj)
            
            # Check if we've seen this combination of properties before
            if object_signature not in self.object_patterns:
                discovery_id = f"DISC_{self.next_discovery_id:04d}"
                self.next_discovery_id += 1
                
                # Determine discovery type based on object properties
                discovery_type = self._classify_object_discovery(new_obj)
                
                discovery = Discovery(
                    id=discovery_id,
                    discovery_type=discovery_type,
                    name=f"Discovery of {new_obj.name}",
                    description=f"Created {new_obj.name} with properties: {list(new_obj.properties.keys())}",
                    significance=result.significance_score,
                    objects_involved=[obj.name for obj in result.modified_objects + result.destroyed_objects],
                    properties_involved=list(new_obj.properties.keys()),
                    timestamp=tick,
                    discoverer_id=discoverer_id,
                    reproducible=False  # We'll determine this later
                )
                
                # Track the pattern for future reference
                self.object_patterns[object_signature] = {
                    'first_seen': tick,
                    'times_created': 1,
                    'creation_methods': [result.description]
                }
                
                return discovery
            else:
                # This pattern exists, but increment creation count
                self.object_patterns[object_signature]['times_created'] += 1
                if result.description not in self.object_patterns[object_signature]['creation_methods']:
                    self.object_patterns[object_signature]['creation_methods'].append(result.description)
                
                # If created multiple times, mark as reproducible
                if self.object_patterns[object_signature]['times_created'] >= 3:
                    for disc in self.discoveries.values():
                        if disc.name == f"Discovery of {new_obj.name}":
                            disc.reproducible = True
                            break
        
        return None
    
    def _detect_property_discovery(self, result: CombinationResult, 
                                  tick: int, discoverer_id: str) -> Optional[Discovery]:
        """Detect when objects gain new or unusual property combinations"""
        
        for obj in result.modified_objects:
            # Look for new properties that just appeared
            new_properties = []
            
            # This is simplified - in practice we'd track object history
            state_properties = [name for name, prop in obj.properties.items() 
                              if not prop.is_permanent]
            
            if state_properties:
                for prop_name in state_properties:
                    prop_key = f"{obj.name}_{prop_name}"
                    if prop_key not in self.property_emergence:
                        self.property_emergence[prop_key] = {
                            'first_seen': tick,
                            'context': result.description,
                            'significance': result.significance_score
                        }
                        new_properties.append(prop_name)
                
                if new_properties and result.significance_score > self.significance_threshold * 0.8:
                    discovery_id = f"PROP_{self.next_discovery_id:04d}"
                    self.next_discovery_id += 1
                    
                    return Discovery(
                        id=discovery_id,
                        discovery_type=DiscoveryType.PROPERTY_COMBINATION,
                        name=f"New properties on {obj.name}",
                        description=f"{obj.name} gained: {', '.join(new_properties)}",
                        significance=result.significance_score,
                        objects_involved=[obj.name],
                        properties_involved=new_properties,
                        timestamp=tick,
                        discoverer_id=discoverer_id
                    )
        
        return None
    
    def _detect_tool_discovery(self, result: CombinationResult, 
                              tick: int, discoverer_id: str) -> Optional[Discovery]:
        """Detect when a functional tool is created"""
        
        for new_obj in result.new_objects:
            if self._is_functional_tool(new_obj):
                discovery_id = f"TOOL_{self.next_discovery_id:04d}"
                self.next_discovery_id += 1
                
                return Discovery(
                    id=discovery_id,
                    discovery_type=DiscoveryType.TOOL_CREATION,
                    name=f"Tool Creation: {new_obj.name}",
                    description=f"Functional tool created with capabilities: {self._describe_tool_capabilities(new_obj)}",
                    significance=result.significance_score + 5.0,  # Tools are extra significant
                    objects_involved=[obj.name for obj in result.modified_objects + result.destroyed_objects],
                    properties_involved=list(new_obj.properties.keys()),
                    timestamp=tick,
                    discoverer_id=discoverer_id
                )
        
        return None
    
    def _get_object_signature(self, obj: UniverseObject) -> str:
        """Create a unique signature for an object based on its properties"""
        props = sorted(obj.properties.keys())
        return f"{obj.name}::{':'.join(props)}"
    
    def _classify_object_discovery(self, obj: UniverseObject) -> DiscoveryType:
        """Classify what type of discovery this object represents"""
        
        if self._is_functional_tool(obj):
            return DiscoveryType.TOOL_CREATION
        elif len(obj.properties) > 3:  # Complex object
            return DiscoveryType.COMPOUND_CREATION
        else:
            return DiscoveryType.NEW_OBJECT
    
    def _is_tool_creation(self, result: CombinationResult) -> bool:
        """Check if this result represents tool creation"""
        return any(self._is_functional_tool(obj) for obj in result.new_objects)
    
    def _is_functional_tool(self, obj: UniverseObject) -> bool:
        """Determine if an object is a functional tool"""
        tool_properties = ["es_puntiagudo", "es_cortante", "es_duro"]
        return any(obj.has_property(prop) for prop in tool_properties)
    
    def _describe_tool_capabilities(self, tool: UniverseObject) -> str:
        """Describe what a tool can do"""
        capabilities = []
        
        if tool.has_property("es_puntiagudo"):
            capabilities.append("piercing")
        if tool.has_property("es_cortante"):
            capabilities.append("cutting")
        if tool.has_property("es_duro"):
            capabilities.append("striking")
        if tool.has_property("brilla"):
            capabilities.append("illumination")
        
        return ", ".join(capabilities) if capabilities else "unknown"
    
    def _update_knowledge_base(self, discovery: Discovery, result: CombinationResult):
        """Update our knowledge base with this discovery"""
        
        # Track interaction chains that lead to discoveries
        if len(self.interaction_chains) > 0:
            discovery.interaction_sequence = self.interaction_chains[-5:]  # Last 5 interactions
        
        # Mark breakthrough discoveries
        if discovery.significance > self.significance_threshold * 2:
            discovery.discovery_type = DiscoveryType.BREAKTHROUGH
    
    def record_interaction_chain(self, interaction_description: str):
        """Record an interaction in the chain"""
        self.interaction_chains.append(interaction_description)
        
        # Keep only recent interactions
        if len(self.interaction_chains) > 20:
            self.interaction_chains = self.interaction_chains[-20:]
    
    def get_discovery_by_id(self, discovery_id: str) -> Optional[Discovery]:
        """Get a specific discovery by ID"""
        return self.discoveries.get(discovery_id)
    
    def get_discoveries_by_type(self, discovery_type: DiscoveryType) -> List[Discovery]:
        """Get all discoveries of a specific type"""
        return [d for d in self.discoveries.values() if d.discovery_type == discovery_type]
    
    def get_recent_discoveries(self, count: int = 10) -> List[Discovery]:
        """Get the most recent discoveries"""
        sorted_discoveries = sorted(self.discoveries.values(), 
                                  key=lambda d: d.timestamp, reverse=True)
        return sorted_discoveries[:count]
    
    def get_most_significant_discoveries(self, count: int = 10) -> List[Discovery]:
        """Get the most significant discoveries"""
        sorted_discoveries = sorted(self.discoveries.values(), 
                                  key=lambda d: d.significance, reverse=True)
        return sorted_discoveries[:count]
    
    def mark_discovery_application(self, discovery_id: str, application: str):
        """Mark how a discovery has been applied/used"""
        if discovery_id in self.discoveries:
            if application not in self.discoveries[discovery_id].applications:
                self.discoveries[discovery_id].applications.append(application)
    
    def generate_discovery_report(self) -> str:
        """Generate a comprehensive discovery report"""
        if not self.discoveries:
            return "=== DISCOVERY REPORT ===\nNo discoveries made yet.\n"
        
        report = "=== DISCOVERY REPORT ===\n\n"
        
        # Summary statistics
        total = len(self.discoveries)
        by_type = {}
        for disc in self.discoveries.values():
            by_type[disc.discovery_type.value] = by_type.get(disc.discovery_type.value, 0) + 1
        
        report += f"Total Discoveries: {total}\n"
        report += "By Type:\n"
        for disc_type, count in by_type.items():
            report += f"  {disc_type.replace('_', ' ').title()}: {count}\n"
        report += "\n"
        
        # Most significant discoveries
        significant = self.get_most_significant_discoveries(5)
        report += "=== MOST SIGNIFICANT DISCOVERIES ===\n"
        for disc in significant:
            report += f"\n{disc.name} (ID: {disc.id})\n"
            report += f"  Type: {disc.discovery_type.value.replace('_', ' ').title()}\n"
            report += f"  Significance: {disc.significance:.1f}\n"
            report += f"  Description: {disc.description}\n"
            if disc.reproducible:
                report += f"  Status: REPRODUCIBLE ✓\n"
            if disc.applications:
                report += f"  Applications: {', '.join(disc.applications)}\n"
        
        # Recent breakthroughs
        breakthroughs = self.get_discoveries_by_type(DiscoveryType.BREAKTHROUGH)
        if breakthroughs:
            report += "\n=== BREAKTHROUGH DISCOVERIES ===\n"
            for disc in breakthroughs:
                report += f"\n🎉 {disc.name}\n"
                report += f"   {disc.description}\n"
                report += f"   Significance: {disc.significance:.1f}\n"
        
        return report
    
    def export_discoveries_to_json(self, filename: str):
        """Export all discoveries to a JSON file"""
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_discoveries': len(self.discoveries),
                'next_id': self.next_discovery_id
            },
            'discoveries': {}
        }
        
        for disc_id, disc in self.discoveries.items():
            export_data['discoveries'][disc_id] = {
                'id': disc.id,
                'type': disc.discovery_type.value,
                'name': disc.name,
                'description': disc.description,
                'significance': disc.significance,
                'objects_involved': disc.objects_involved,
                'properties_involved': disc.properties_involved,
                'timestamp': disc.timestamp,
                'discoverer_id': disc.discoverer_id,
                'reproducible': disc.reproducible,
                'applications': disc.applications
            }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get a summary of accumulated knowledge"""
        return {
            'total_discoveries': len(self.discoveries),
            'unique_object_patterns': len(self.object_patterns),
            'property_emergences': len(self.property_emergence),
            'reproducible_discoveries': len([d for d in self.discoveries.values() if d.reproducible]),
            'breakthrough_count': len(self.get_discoveries_by_type(DiscoveryType.BREAKTHROUGH)),
            'most_creative_discoverer': self._get_most_creative_discoverer()
        }
    
    def _get_most_creative_discoverer(self) -> Optional[str]:
        """Find which entity has made the most discoveries"""
        discoverer_counts = {}
        for disc in self.discoveries.values():
            if disc.discoverer_id:
                discoverer_counts[disc.discoverer_id] = discoverer_counts.get(disc.discoverer_id, 0) + 1
        
        if discoverer_counts:
            return max(discoverer_counts.items(), key=lambda x: x[1])[0]
        return None

# Global discovery system instance
DISCOVERY_DETECTOR = DiscoveryDetector()