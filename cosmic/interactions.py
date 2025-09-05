from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math
from .objects import UniverseObject, CombinationResult
from .properties import PropertyValue, PropertyType, PROPERTY_REGISTRY

class InteractionType(Enum):
    """Types of interactions between objects"""
    COMBINE = "combine"      # Merge objects together
    STRIKE = "strike"        # Hit one object with another
    APPLY = "apply"          # Apply one object to another
    MIX = "mix"              # Mix substances together
    HEAT = "heat"            # Apply heat
    COOL = "cool"            # Remove heat
    PRESSURE = "pressure"    # Apply pressure/force
    TOUCH = "touch"          # Gentle contact

@dataclass
class InteractionRule:
    """Defines what happens when specific properties interact"""
    trigger_properties: List[str]  # Properties that must be present
    target_properties: List[str]   # Properties the target must have
    action_type: InteractionType
    result_function: Callable
    probability: float = 1.0       # Chance this rule triggers (0.0-1.0)
    requires_tool: bool = False    # Does this need a tool/intermediary?
    description: str = ""

class InteractionEngine:
    """The universal motor that handles ALL object interactions"""
    
    def __init__(self):
        self.rules = []
        self.interaction_history = []
        self.discovered_combinations = {}  # Track successful combinations
        self.failed_attempts = {}         # Track what doesn't work
        self._initialize_base_rules()
    
    def _initialize_base_rules(self):
        """Initialize fundamental interaction rules of physics"""
        
        # Basic physical rules
        self.add_rule(
            trigger_properties=["es_cortante"],
            target_properties=["es_fragil"],
            action_type=InteractionType.STRIKE,
            result_function=self._rule_cutting,
            description="Sharp objects can cut fragile materials"
        )
        
        self.add_rule(
            trigger_properties=["es_duro"],
            target_properties=["es_fragil"],
            action_type=InteractionType.STRIKE,
            result_function=self._rule_breaking,
            description="Hard objects can break fragile materials"
        )
        
        # Thermal rules
        self.add_rule(
            trigger_properties=["es_caliente"],
            target_properties=["es_organico"],
            action_type=InteractionType.TOUCH,
            result_function=self._rule_burning,
            description="Heat burns organic materials"
        )
        
        self.add_rule(
            trigger_properties=["es_caliente"],
            target_properties=["es_humedo"],
            action_type=InteractionType.APPLY,
            result_function=self._rule_evaporation,
            description="Heat evaporates moisture"
        )
        
        # Chemical rules
        self.add_rule(
            trigger_properties=["es_acido"],
            target_properties=["es_duro", "es_organico"],
            action_type=InteractionType.APPLY,
            result_function=self._rule_corrosion,
            description="Acid corrodes materials"
        )
        
        self.add_rule(
            trigger_properties=["es_reactivo"],
            target_properties=["es_reactivo"],
            action_type=InteractionType.MIX,
            result_function=self._rule_chemical_reaction,
            probability=0.6,
            description="Reactive materials can undergo chemical reactions"
        )
        
        # Tool creation rules
        self.add_rule(
            trigger_properties=["es_cortante"],
            target_properties=["es_fragil", "es_organico"],
            action_type=InteractionType.PRESSURE,
            result_function=self._rule_tool_creation,
            description="Careful shaping creates pointed tools"
        )
        
        # Biological rules
        self.add_rule(
            trigger_properties=["es_organico"],
            target_properties=["es_organico"],
            action_type=InteractionType.MIX,
            result_function=self._rule_organic_mixing,
            probability=0.3,
            description="Organic materials can sometimes be mixed"
        )
        
        self.add_rule(
            trigger_properties=["es_fermentable"],
            target_properties=["es_organico"],
            action_type=InteractionType.MIX,
            result_function=self._rule_fermentation,
            probability=0.5,
            description="Fermentable materials can create new compounds"
        )
        
        # Energy rules
        self.add_rule(
            trigger_properties=["es_magnetico"],
            target_properties=["conduce_electricidad"],
            action_type=InteractionType.TOUCH,
            result_function=self._rule_electromagnetic_induction,
            description="Magnetic fields can induce electricity"
        )
        
        self.add_rule(
            trigger_properties=["es_piezoelectrico"],
            target_properties=["es_duro"],
            action_type=InteractionType.PRESSURE,
            result_function=self._rule_piezo_effect,
            description="Pressure on piezoelectric materials generates electricity"
        )
        
        self.add_rule(
            trigger_properties=["es_catalizador"],
            target_properties=["es_reactivo"],
            action_type=InteractionType.APPLY,
            result_function=self._rule_catalysis,
            description="Catalysts accelerate reactions"
        )
        
        # Crystal formation
        self.add_rule(
            trigger_properties=["es_solvente"],
            target_properties=["es_cristalino"],
            action_type=InteractionType.MIX,
            result_function=self._rule_crystallization,
            probability=0.4,
            description="Solvents can dissolve and reform crystals"
        )
        
        # Explosive reactions
        self.add_rule(
            trigger_properties=["es_explosivo"],
            target_properties=["es_caliente", "es_reactivo"],
            action_type=InteractionType.APPLY,
            result_function=self._rule_explosion,
            probability=0.8,
            description="Explosive materials react violently with heat or reactants"
        )
        
        # Advanced material creation
        self.add_rule(
            trigger_properties=["conduce_electricidad"],
            target_properties=["es_magnetico"],
            action_type=InteractionType.COMBINE,
            result_function=self._rule_advanced_conductor,
            probability=0.3,
            description="Combining conductive and magnetic materials creates advanced properties"
        )
    
    def add_rule(self, trigger_properties: List[str], target_properties: List[str],
                 action_type: InteractionType, result_function: Callable,
                 probability: float = 1.0, requires_tool: bool = False, description: str = ""):
        """Add a new interaction rule to the engine"""
        rule = InteractionRule(
            trigger_properties=trigger_properties,
            target_properties=target_properties,
            action_type=action_type,
            result_function=result_function,
            probability=probability,
            requires_tool=requires_tool,
            description=description
        )
        self.rules.append(rule)
    
    def interact(self, actor: UniverseObject, target: UniverseObject, 
                action: str = "combine", tool: Optional[UniverseObject] = None) -> CombinationResult:
        """Universal interaction function - the heart of discovery"""
        
        result = CombinationResult()
        interaction_type = InteractionType(action.lower())
        
        # Log this interaction attempt
        self._log_interaction(actor, target, interaction_type, tool)
        
        # Find applicable rules
        applicable_rules = self._find_applicable_rules(actor, target, interaction_type, tool)
        
        if not applicable_rules:
            # No specific rule - try generic interaction
            return self._generic_interaction(actor, target, interaction_type)
        
        # Apply the best matching rule
        best_rule = self._select_best_rule(applicable_rules, actor, target)
        
        if random.random() <= best_rule.probability:
            result = best_rule.result_function(actor, target, tool, result)
            result.success = True
            result.description = f"{best_rule.description}: {actor.name} + {target.name}"
        else:
            result.description = f"Interaction between {actor.name} and {target.name} failed"
        
        # Calculate significance and store result
        result.calculate_significance()
        self._store_interaction_result(actor, target, interaction_type, result)
        
        return result
    
    def _find_applicable_rules(self, actor: UniverseObject, target: UniverseObject,
                              interaction_type: InteractionType, tool: Optional[UniverseObject]) -> List[InteractionRule]:
        """Find all rules that could apply to this interaction"""
        applicable_rules = []
        
        for rule in self.rules:
            if rule.action_type != interaction_type:
                continue
            
            # Check if actor has required trigger properties
            actor_has_triggers = all(actor.has_property(prop) for prop in rule.trigger_properties)
            
            # Check if target has required target properties
            target_has_properties = any(target.has_property(prop) for prop in rule.target_properties)
            
            # Check tool requirement
            if rule.requires_tool and tool is None:
                continue
            
            if actor_has_triggers and target_has_properties:
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _select_best_rule(self, rules: List[InteractionRule], actor: UniverseObject, 
                         target: UniverseObject) -> InteractionRule:
        """Select the most appropriate rule from applicable ones"""
        if len(rules) == 1:
            return rules[0]
        
        # Score rules based on property matching and specificity
        scored_rules = []
        
        for rule in rules:
            score = 0
            
            # Score for exact property matches
            for prop in rule.trigger_properties:
                if actor.has_property(prop):
                    score += actor.get_property(prop).intensity * 10
            
            for prop in rule.target_properties:
                if target.has_property(prop):
                    score += target.get_property(prop).intensity * 5
            
            # Bonus for more specific rules (more required properties)
            score += len(rule.trigger_properties) + len(rule.target_properties)
            
            scored_rules.append((score, rule))
        
        # Return the highest scoring rule
        scored_rules.sort(key=lambda x: x[0], reverse=True)
        return scored_rules[0][1]
    
    def _generic_interaction(self, actor: UniverseObject, target: UniverseObject,
                           interaction_type: InteractionType) -> CombinationResult:
        """Handle interactions that don't match specific rules"""
        result = CombinationResult()
        
        # Basic physical interactions
        if interaction_type == InteractionType.STRIKE:
            damage = max(1, int(actor.get_interaction_strength() - target.state.durability * 0.1))
            target.take_damage(damage)
            result.add_modified_object(target)
            result.description = f"{actor.name} strikes {target.name} for {damage} damage"
            result.success = damage > 0
        
        elif interaction_type == InteractionType.TOUCH:
            # Temperature exchange
            temp_diff = actor.state.temperature - target.state.temperature
            if abs(temp_diff) > 10:
                transfer = temp_diff * 0.1
                actor.change_temperature(-transfer)
                target.change_temperature(transfer)
                result.add_modified_object(actor)
                result.add_modified_object(target)
                result.description = f"Temperature exchange between {actor.name} and {target.name}"
                result.success = True
        
        elif interaction_type == InteractionType.COMBINE:
            # Simple combination - objects just touch and maybe exchange properties
            if random.random() < 0.1:  # 10% chance of something happening
                self._random_property_exchange(actor, target, result)
        
        return result
    
    def _random_property_exchange(self, actor: UniverseObject, target: UniverseObject,
                                 result: CombinationResult):
        """Sometimes objects can randomly exchange or gain properties"""
        
        # Transfer a temporary property
        transferable_props = [name for name, prop in actor.properties.items() 
                             if not prop.is_permanent and prop.intensity > 0.3]
        
        if transferable_props and random.random() < 0.5:
            prop_name = random.choice(transferable_props)
            actor_prop = actor.get_property(prop_name)
            
            # Transfer some intensity
            transfer_amount = actor_prop.intensity * 0.3
            target.add_property(prop_name, transfer_amount)
            actor.modify_property_intensity(prop_name, -transfer_amount)
            
            result.add_modified_object(actor)
            result.add_modified_object(target)
            result.description = f"{prop_name} transferred from {actor.name} to {target.name}"
            result.success = True
    
    # ========== INTERACTION RULE FUNCTIONS ==========
    
    def _rule_cutting(self, actor: UniverseObject, target: UniverseObject, 
                     tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for cutting fragile materials with sharp objects"""
        
        sharpness = actor.get_property("es_cortante").intensity
        target_resistance = target.get_property("es_fragil").intensity
        
        if sharpness > target_resistance:
            # Successful cutting - modify target
            target.add_property("esta_roto")
            
            # If cutting organic material, might create useful pieces
            if target.has_property("es_organico"):
                if random.random() < 0.6:  # 60% chance
                    # Create a sharpened version
                    new_object = UniverseObject(f"{target.name} Puntiagudo", 
                                               ["es_organico", "es_puntiagudo", "es_fragil"])
                    new_object.x, new_object.y = target.x, target.y
                    result.add_new_object(new_object)
            
            damage = int(sharpness * 20)
            target.take_damage(damage)
            result.add_modified_object(target)
        
        return result
    
    def _rule_breaking(self, actor: UniverseObject, target: UniverseObject,
                      tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for breaking fragile materials with hard objects"""
        
        hardness = actor.get_property("es_duro").intensity
        fragility = target.get_property("es_fragil").intensity
        
        damage = int(hardness * fragility * 25)
        destroyed = target.take_damage(damage)
        
        if destroyed:
            result.add_destroyed_object(target)
        else:
            result.add_modified_object(target)
            target.add_property("esta_roto")
        
        return result
    
    def _rule_burning(self, actor: UniverseObject, target: UniverseObject,
                     tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for burning organic materials"""
        
        heat = actor.get_property("es_caliente").intensity
        
        # Burn the target
        target.add_property("esta_quemado")
        target.change_temperature(heat * 50)  # Heat transfer
        
        damage = int(heat * 30)
        target.take_damage(damage)
        
        result.add_modified_object(target)
        
        # Burning might create ash or charcoal
        if random.random() < 0.3:
            ash = UniverseObject("Ceniza", ["es_organico", "es_fragil"])
            ash.x, ash.y = target.x, target.y
            result.add_new_object(ash)
        
        return result
    
    def _rule_evaporation(self, actor: UniverseObject, target: UniverseObject,
                         tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for evaporating moisture"""
        
        target.remove_property("es_humedo")
        target.remove_property("esta_mojado")
        
        # Might leave behind concentrated materials
        if target.has_property("es_nutritivo") and random.random() < 0.4:
            concentrated = UniverseObject(f"{target.name} Concentrado", 
                                        [prop for prop in target.properties.keys() 
                                         if prop not in ["es_humedo", "esta_mojado"]])
            concentrated.add_property("es_concentrado")  # New emergent property!
            concentrated.x, concentrated.y = target.x, target.y
            result.add_new_object(concentrated)
        
        result.add_modified_object(target)
        return result
    
    def _rule_corrosion(self, actor: UniverseObject, target: UniverseObject,
                       tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for acid corroding materials"""
        
        acid_strength = actor.get_property("es_acido").intensity
        
        # Acid damages over time
        damage = int(acid_strength * 15)
        target.take_damage(damage)
        
        # Might weaken hard materials
        if target.has_property("es_duro"):
            target.modify_property_intensity("es_duro", -0.2)
        
        result.add_modified_object(target)
        return result
    
    def _rule_tool_creation(self, actor: UniverseObject, target: UniverseObject,
                           tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for creating pointed tools through careful shaping"""
        
        # This is a more complex interaction - creating something NEW
        if target.has_property("es_organico") and target.has_property("es_fragil"):
            
            # Success depends on sharpness and control
            sharpness = actor.get_property("es_cortante").intensity
            
            if sharpness > 0.6 and random.random() < 0.7:  # Need good tools and skill
                # Create a primitive spear!
                spear = UniverseObject("Lanza Primitiva", 
                                     ["es_organico", "es_puntiagudo", "es_liviano"])
                spear.state.durability = int(target.state.durability * 0.8)  # Slightly weaker
                spear.x, spear.y = target.x, target.y
                
                # This is significant! A new tool concept
                result.add_new_object(spear)
                result.significance_score += 15.0  # Tool creation is very significant
                
                # Target is consumed in the process
                result.add_destroyed_object(target)
        
        return result
    
    def _rule_organic_mixing(self, actor: UniverseObject, target: UniverseObject,
                            tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for mixing organic materials - can create new substances"""
        
        # Mixing organic materials can create new compounds
        if random.random() < 0.4:  # 40% chance of success
            
            # Combine properties from both materials
            new_properties = []
            
            # Keep common beneficial properties
            if actor.has_property("es_nutritivo") and target.has_property("es_nutritivo"):
                new_properties.append("es_nutritivo")
            
            # Dangerous combinations
            if (actor.has_property("es_venenoso") or target.has_property("es_venenoso")):
                new_properties.extend(["es_organico", "es_venenoso"])
            else:
                new_properties.append("es_organico")
            
            # Random chance of creating something special
            if random.random() < 0.1:  # 10% chance
                special_properties = ["brilla", "es_concentrado", "conduce_electricidad"]
                new_properties.append(random.choice(special_properties))
            
            # Create the mixture
            mixture_name = f"Mezcla de {actor.name} y {target.name}"
            mixture = UniverseObject(mixture_name, new_properties)
            mixture.x, mixture.y = (actor.x + target.x) // 2, (actor.y + target.y) // 2
            
            result.add_new_object(mixture)
            
            # Both originals are consumed
            result.add_destroyed_object(actor)
            result.add_destroyed_object(target)
        
        return result
    
    def _rule_chemical_reaction(self, actor: UniverseObject, target: UniverseObject,
                               tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for reactive materials combining"""
        
        # Create a new compound with combined properties
        compound_properties = []
        
        # Combine reactive properties
        if actor.has_property("es_acido") and target.has_property("es_alcalino"):
            # Acid + Base = Salt + neutralization
            compound_properties.extend(["es_estable", "es_cristalino"])
        elif actor.has_property("es_explosivo") or target.has_property("es_explosivo"):
            # Explosive reactions create energy
            compound_properties.extend(["es_reactivo", "brilla", "es_caliente"])
        else:
            # Generic reactive combination
            compound_properties.extend(["es_reactivo", "es_hibrido"])
        
        if random.random() < 0.3:  # 30% chance of special properties
            special = ["es_catalizador", "es_solvente", "conduce_electricidad"]
            compound_properties.append(random.choice(special))
        
        # Create new compound
        compound_name = f"Compuesto de {actor.name} y {target.name}"
        compound = UniverseObject(compound_name, compound_properties)
        compound.x, compound.y = (actor.x + target.x) // 2, (actor.y + target.y) // 2
        
        result.add_new_object(compound)
        result.add_destroyed_object(actor)
        result.add_destroyed_object(target)
        
        return result
    
    def _rule_fermentation(self, actor: UniverseObject, target: UniverseObject,
                          tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for fermentation creating new compounds"""
        
        # Fermentation creates alcohol, acids, or gases
        fermentation_products = [
            ("Alcohol", ["es_organico", "es_inflamable", "es_toxico"]),
            ("Vinagre", ["es_organico", "es_acido", "es_solvente"]),
            ("Gas Metano", ["es_inflamable", "es_explosivo", "vibra"]),
            ("Enzima", ["es_organico", "es_catalizador", "es_fragil"])
        ]
        
        product_name, properties = random.choice(fermentation_products)
        product = UniverseObject(product_name, properties)
        product.x, product.y = target.x, target.y
        
        result.add_new_object(product)
        result.add_modified_object(target)  # Original material is partially consumed
        
        return result
    
    def _rule_electromagnetic_induction(self, actor: UniverseObject, target: UniverseObject,
                                       tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for magnetic induction creating electricity"""
        
        # Magnetic + Conductive = Electric field
        target.add_property("esta_cargado")
        target.add_property("genera_campo")
        
        if random.random() < 0.4:  # 40% chance of creating a generator
            generator = UniverseObject("Generador Primitivo", 
                                     ["conduce_electricidad", "es_magnetico", "genera_campo"])
            generator.x, generator.y = target.x, target.y
            result.add_new_object(generator)
        
        result.add_modified_object(target)
        return result
    
    def _rule_piezo_effect(self, actor: UniverseObject, target: UniverseObject,
                          tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for piezoelectric effect generating electricity"""
        
        target.add_property("esta_cargado")
        target.add_property("brilla")  # Electrical discharge creates light
        
        # Might create a battery-like object
        if random.random() < 0.3:
            battery = UniverseObject("Bateria Cristalina", 
                                   ["es_piezoelectrico", "conduce_electricidad", "es_cristalino"])
            battery.x, battery.y = target.x, target.y
            result.add_new_object(battery)
        
        result.add_modified_object(target)
        return result
    
    def _rule_catalysis(self, actor: UniverseObject, target: UniverseObject,
                       tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for catalytic reactions"""
        
        # Catalyst accelerates reactions - creates more refined products
        if target.has_property("es_organico"):
            # Organic catalysis
            refined_products = [
                ("Proteina Pura", ["es_organico", "es_nutritivo", "esta_purificado"]),
                ("Aceite Refinado", ["es_organico", "es_inflamable", "es_viscoso"]),
                ("Fibra Procesada", ["es_organico", "es_flexible", "es_duro"])
            ]
        else:
            # Inorganic catalysis
            refined_products = [
                ("Metal Puro", ["es_duro", "conduce_electricidad", "esta_purificado"]),
                ("Cristal Perfecto", ["es_cristalino", "brilla", "es_duro"]),
                ("Ceramica", ["es_duro", "es_incombustible", "es_cristalino"])
            ]
        
        product_name, properties = random.choice(refined_products)
        product = UniverseObject(product_name, properties)
        product.x, product.y = target.x, target.y
        
        result.add_new_object(product)
        result.add_modified_object(target)  # Catalyst is not consumed
        
        return result
    
    def _rule_crystallization(self, actor: UniverseObject, target: UniverseObject,
                             tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for crystal formation and dissolution"""
        
        if actor.has_property("es_solvente"):
            # Dissolving crystal
            if random.random() < 0.6:  # 60% chance to reform as better crystal
                crystal_types = [
                    ("Cuarzo", ["es_cristalino", "es_piezoelectrico", "brilla"]),
                    ("Sal Cristalina", ["es_cristalino", "es_solvente", "es_duro"]),
                    ("Gema", ["es_cristalino", "es_duro", "absorbe_luz", "brilla"])
                ]
                
                crystal_name, properties = random.choice(crystal_types)
                crystal = UniverseObject(crystal_name, properties)
                crystal.x, crystal.y = target.x, target.y
                
                result.add_new_object(crystal)
                result.add_destroyed_object(target)
        
        return result
    
    def _rule_explosion(self, actor: UniverseObject, target: UniverseObject,
                       tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for explosive reactions"""
        
        # Create explosion effects
        explosion = UniverseObject("Explosion", ["es_caliente", "brilla", "vibra"])
        explosion.x, explosion.y = actor.x, actor.y
        explosion.state.temperature = 1000.0  # Very hot
        
        result.add_new_object(explosion)
        result.add_destroyed_object(actor)
        
        # Explosion might create fragments or new materials
        if random.random() < 0.5:
            fragment_types = [
                ("Fragmentos Metalicos", ["es_duro", "es_cortante", "conduce_electricidad"]),
                ("Ceniza Reactiva", ["es_organico", "es_reactivo", "es_fragil"]),
                ("Plasma", ["brilla", "es_caliente", "conduce_electricidad", "vibra"])
            ]
            
            fragment_name, properties = random.choice(fragment_types)
            fragment = UniverseObject(fragment_name, properties)
            fragment.x, fragment.y = actor.x, actor.y
            result.add_new_object(fragment)
        
        # High damage to surroundings (simplified - would affect nearby objects)
        if target:
            target.take_damage(80)
            result.add_modified_object(target)
        
        return result
    
    def _rule_advanced_conductor(self, actor: UniverseObject, target: UniverseObject,
                                tool: Optional[UniverseObject], result: CombinationResult) -> CombinationResult:
        """Rule for creating advanced conductive materials"""
        
        # Combining electrical and magnetic properties creates advanced materials
        advanced_materials = [
            ("Superconductor", ["es_superconductor", "es_frio", "conduce_electricidad"]),
            ("Electromagneto", ["conduce_electricidad", "es_magnetico", "genera_campo"]),
            ("Bobina de Induccion", ["conduce_electricidad", "es_magnetico", "vibra", "genera_campo"])
        ]
        
        material_name, properties = random.choice(advanced_materials)
        material = UniverseObject(material_name, properties)
        material.x, material.y = (actor.x + target.x) // 2, (actor.y + target.y) // 2
        
        result.add_new_object(material)
        result.add_destroyed_object(actor)
        result.add_destroyed_object(target)
        
        # This is a major technological breakthrough
        result.significance_score += 20.0
        
        return result
    
    # ========== UTILITY METHODS ==========
    
    def _log_interaction(self, actor: UniverseObject, target: UniverseObject,
                        interaction_type: InteractionType, tool: Optional[UniverseObject]):
        """Log an interaction attempt"""
        log_entry = {
            'actor': actor.name,
            'target': target.name,
            'action': interaction_type.value,
            'tool': tool.name if tool else None,
            'timestamp': len(self.interaction_history)
        }
        self.interaction_history.append(log_entry)
    
    def _store_interaction_result(self, actor: UniverseObject, target: UniverseObject,
                                 interaction_type: InteractionType, result: CombinationResult):
        """Store the result of an interaction for learning"""
        key = (actor.name, target.name, interaction_type.value)
        
        if result.success:
            if key not in self.discovered_combinations:
                self.discovered_combinations[key] = []
            self.discovered_combinations[key].append(result)
        else:
            if key not in self.failed_attempts:
                self.failed_attempts[key] = 0
            self.failed_attempts[key] += 1
    
    def get_interaction_statistics(self) -> Dict[str, Any]:
        """Get statistics about interactions that have occurred"""
        return {
            'total_interactions': len(self.interaction_history),
            'successful_combinations': len(self.discovered_combinations),
            'failed_attempts': sum(self.failed_attempts.values()),
            'most_successful_combinations': sorted(
                self.discovered_combinations.keys(),
                key=lambda k: len(self.discovered_combinations[k]),
                reverse=True
            )[:5]
        }
    
    def get_discovery_report(self) -> str:
        """Generate a report of all discoveries made"""
        report = "=== DISCOVERY REPORT ===\n"
        
        if not self.discovered_combinations:
            return report + "No successful combinations discovered yet.\n"
        
        for (actor, target, action), results in self.discovered_combinations.items():
            report += f"\n{actor} + {target} ({action}):\n"
            
            for i, result in enumerate(results[:3]):  # Show up to 3 examples
                report += f"  - {result.description}\n"
                if result.new_objects:
                    for obj in result.new_objects:
                        report += f"    Created: {obj}\n"
            
            if len(results) > 3:
                report += f"  ... and {len(results) - 3} more discoveries\n"
        
        return report

# Global interaction engine instance
INTERACTION_ENGINE = InteractionEngine()