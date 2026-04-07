"""
Smart Enemy Generation System
AI-assisted enemy design, evolution, and procedural stats
"""

import json
import math
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..body_families.keywords import get_body_type_keywords
from ..utils.constants import EnemyBodyTypes, EnemyTypes


@dataclass
class EnemyStats:
    """Auto-generated enemy statistics"""
    health: int
    damage: int
    speed: float
    armor: int
    size_modifier: float
    threat_level: str
    special_abilities: List[str]
    weaknesses: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'health': self.health,
            'damage': self.damage, 
            'speed': self.speed,
            'armor': self.armor,
            'size_modifier': self.size_modifier,
            'threat_level': self.threat_level,
            'special_abilities': self.special_abilities,
            'weaknesses': self.weaknesses
        }


@dataclass 
class EnemyBlueprint:
    """Complete enemy design specification"""
    name: str
    description: str
    body_type: str
    enemy_type: str
    material_theme: List[str]
    size_scale: float
    animation_set: str
    stats: EnemyStats
    generation_seed: int
    parent_genes: Optional[List[str]] = None
    # Advanced material options
    material_preset: Optional[str] = None  # Preset like 'battle_worn', 'volcanic_forged'
    environment: Optional[str] = None      # Environmental adaptation  
    damage_level: float = 0.0             # Battle damage 0.0-1.0
    magical_effects: Optional[str] = None  # Magical enhancement type


class TextToEnemyGenerator:
    """Generate enemies from text descriptions using pattern matching"""

    # Keyword mappings for intelligent parsing (single source: body_families.registry)
    BODY_TYPE_KEYWORDS = get_body_type_keywords()
    
    SIZE_KEYWORDS = {
        'tiny': 0.5, 'small': 0.7, 'normal': 1.0, 'medium': 1.0,
        'large': 1.4, 'big': 1.4, 'huge': 2.0, 'giant': 2.5, 'massive': 3.0
    }
    
    MATERIAL_KEYWORDS = {
        'fire': ['fire_orange', 'ember_red', 'bone_white'],
        'ice': ['ice_white', 'frost_blue', 'crystal_purple'],
        'toxic': ['toxic_green', 'slime_green', 'organic_brown'],
        'metal': ['chrome_silver', 'metal_gray', 'rust_orange'],
        'stone': ['stone_gray', 'dirt_brown', 'rust_orange'],
        'organic': ['flesh_pink', 'organic_brown', 'blood_red'],
        'dark': ['tar_black', 'rot_purple', 'bone_white']
    }
    
    def __init__(self):
        self.rng = random.Random()
    
    def generate_from_description(self, description: str, seed: Optional[int] = None) -> EnemyBlueprint:
        """Generate enemy from text description"""
        if seed:
            self.rng.seed(seed)
        
        description_lower = description.lower()
        
        # Extract enemy name
        name = self._extract_name(description)
        
        # Determine body type from description
        body_type = self._determine_body_type(description_lower)
        
        # Choose closest existing enemy type
        enemy_type = self._choose_enemy_type(description_lower, body_type)
        
        # Extract size information
        size_scale = self._determine_size(description_lower)
        
        # Determine material theme
        material_theme = self._determine_materials(description_lower)
        
        # Detect advanced material options
        material_preset = self._detect_material_preset(description_lower)
        environment = self._detect_environment(description_lower)
        damage_level = self._detect_damage_level(description_lower)
        magical_effects = self._detect_magical_effects(description_lower)
        
        # Generate procedural stats based on description
        stats = self._generate_stats(description_lower, size_scale, body_type)
        
        # Choose animation set based on complexity
        animation_set = 'all' if 'boss' in description_lower or 'powerful' in description_lower else 'core'
        
        return EnemyBlueprint(
            name=name,
            description=description,
            body_type=body_type,
            enemy_type=enemy_type,
            material_theme=material_theme,
            size_scale=size_scale,
            animation_set=animation_set,
            stats=stats,
            generation_seed=seed or self.rng.randint(0, 999999),
            material_preset=material_preset,
            environment=environment,
            damage_level=damage_level,
            magical_effects=magical_effects
        )
    
    def _extract_name(self, description: str) -> str:
        """Extract or generate enemy name from description"""
        # Look for quoted names or capitalize first distinctive word
        words = description.split()
        
        # If description starts with "a" or "an", skip those
        start_idx = 1 if words and words[0].lower() in ['a', 'an'] else 0
        
        # Take first few distinctive words
        name_words = []
        for word in words[start_idx:start_idx+2]:
            cleaned = re.sub(r'[^a-zA-Z]', '', word)
            if cleaned and len(cleaned) > 2:
                name_words.append(cleaned.capitalize())
        
        return '_'.join(name_words) or 'Generated_Enemy'
    
    def _determine_body_type(self, description: str) -> str:
        """Determine body type from description keywords"""
        scores = {body_type: 0 for body_type in self.BODY_TYPE_KEYWORDS}
        
        for body_type, keywords in self.BODY_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description:
                    scores[body_type] += 1
        
        # Return highest scoring body type, default to quadruped
        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else EnemyBodyTypes.QUADRUPED
    
    def _choose_enemy_type(self, description: str, body_type: str) -> str:
        """Choose existing enemy type that best matches description and body type"""
        # Map body types to compatible enemy types
        compatible_types = {
            EnemyBodyTypes.BLOB: [EnemyTypes.SLUG],
            EnemyBodyTypes.QUADRUPED: [EnemyTypes.SPIDER], 
            EnemyBodyTypes.HUMANOID: [EnemyTypes.IMP]
        }
        
        # Get compatible types for this body type
        options = compatible_types.get(body_type, [EnemyTypes.SPIDER])
        
        # For now, return the first option (could be made smarter)
        return options[0]
    
    def _determine_size(self, description: str) -> float:
        """Determine size scale from description"""
        for size_word, scale in self.SIZE_KEYWORDS.items():
            if size_word in description:
                return scale
        
        return 1.0  # Default size
    
    def _determine_materials(self, description: str) -> List[str]:
        """Determine material theme from description"""
        for theme, materials in self.MATERIAL_KEYWORDS.items():
            if theme in description:
                return materials
        
        # Default to organic theme
        return self.MATERIAL_KEYWORDS['organic']
    
    def _generate_stats(self, description: str, size_scale: float, body_type: str) -> EnemyStats:
        """Generate balanced stats based on description and characteristics"""
        
        # Base stats influenced by size
        base_health = int(100 * size_scale)
        base_damage = int(25 * size_scale)
        base_speed = max(0.1, 1.0 / size_scale)  # Bigger = slower
        base_armor = int(10 * math.sqrt(size_scale))
        
        # Keyword modifiers
        modifiers = {
            'powerful': {'damage': 1.5, 'health': 1.3},
            'fast': {'speed': 2.0, 'health': 0.7},
            'armored': {'armor': 2.0, 'speed': 0.7},
            'boss': {'health': 3.0, 'damage': 2.0, 'armor': 1.5},
            'weak': {'health': 0.5, 'damage': 0.5},
            'agile': {'speed': 1.8, 'armor': 0.5},
        }
        
        # Apply modifiers based on description
        final_stats = {
            'health': base_health,
            'damage': base_damage,
            'speed': base_speed,
            'armor': base_armor
        }
        
        for keyword, mods in modifiers.items():
            if keyword in description:
                for stat, multiplier in mods.items():
                    final_stats[stat] = int(final_stats[stat] * multiplier)
        
        # Determine threat level
        total_power = final_stats['health'] + final_stats['damage'] * 2 + final_stats['armor']
        if total_power < 150:
            threat_level = "Low"
        elif total_power < 300:
            threat_level = "Medium"  
        elif total_power < 500:
            threat_level = "High"
        else:
            threat_level = "Boss"
        
        # Generate abilities and weaknesses
        abilities = self._generate_abilities(description, body_type, size_scale)
        weaknesses = self._generate_weaknesses(description, body_type, abilities)
        
        return EnemyStats(
            health=final_stats['health'],
            damage=final_stats['damage'],
            speed=final_stats['speed'],
            armor=final_stats['armor'],
            size_modifier=size_scale,
            threat_level=threat_level,
            special_abilities=abilities,
            weaknesses=weaknesses
        )
    
    def _generate_abilities(self, description: str, body_type: str, size_scale: float) -> List[str]:
        """Generate special abilities based on enemy characteristics"""
        abilities = []
        
        # Body type abilities
        if body_type == EnemyBodyTypes.BLOB:
            abilities.append("Shape Shifting")
            if size_scale > 1.5:
                abilities.append("Area Slam")
        elif body_type == EnemyBodyTypes.QUADRUPED:
            abilities.append("Multi-limb Attack")
            abilities.append("Wall Climbing")
        elif body_type == EnemyBodyTypes.HUMANOID:
            abilities.append("Tool Use")
            abilities.append("Tactical Movement")
        
        # Description-based abilities
        if 'fire' in description:
            abilities.append("Burning Touch")
        if 'ice' in description:
            abilities.append("Frost Aura")
        if 'toxic' in description:
            abilities.append("Poison Cloud")
        if 'fast' in description:
            abilities.append("Speed Burst")
        if 'powerful' in description or 'boss' in description:
            abilities.append("Devastating Attacks")
        
        return abilities[:4]  # Limit to 4 abilities
    
    def _generate_weaknesses(self, description: str, body_type: str, abilities: List[str]) -> List[str]:
        """Generate balanced weaknesses"""
        weaknesses = []
        
        # Counter-elemental weaknesses
        if 'fire' in description or "Burning Touch" in abilities:
            weaknesses.append("Vulnerable to Ice")
        if 'ice' in description or "Frost Aura" in abilities:
            weaknesses.append("Vulnerable to Fire")
        if 'toxic' in description or "Poison Cloud" in abilities:
            weaknesses.append("Vulnerable to Pure Damage")
        
        # Body type weaknesses
        if body_type == EnemyBodyTypes.BLOB:
            weaknesses.append("Piercing Damage")
        elif body_type == EnemyBodyTypes.QUADRUPED:
            weaknesses.append("Area Effects")
        elif body_type == EnemyBodyTypes.HUMANOID:
            weaknesses.append("Stunning Effects")
        
        # Size-based weaknesses
        if description and any(word in description for word in ['huge', 'giant', 'massive']):
            weaknesses.append("Slow Movement")
        if description and any(word in description for word in ['fast', 'agile']):
            weaknesses.append("Low Health")
            
        return weaknesses
    
    def _detect_material_preset(self, description: str) -> Optional[str]:
        """Detect material preset from description"""
        preset_keywords = {
            'battle_worn': ['worn', 'damaged', 'scarred', 'battle-worn', 'weathered', 'veteran'],
            'swamp_corrupted': ['swamp', 'marsh', 'bog', 'corrupt', 'rotting', 'putrid'],
            'volcanic_forged': ['volcanic', 'lava', 'molten', 'forge', 'ember', 'hellish'],
            'ice_cursed': ['frozen', 'cursed', 'arctic', 'glacial', 'frigid', 'frost'],
            'fire_blessed': ['blessed', 'holy fire', 'divine', 'purifying'],
            'shadow_touched': ['shadow', 'dark', 'void', 'cursed', 'nightmare'],
            'toxic_mutated': ['toxic', 'mutated', 'poisonous', 'corrupted', 'diseased']
        }
        
        for preset, keywords in preset_keywords.items():
            if any(keyword in description for keyword in keywords):
                return preset
        return None
    
    def _detect_environment(self, description: str) -> Optional[str]:
        """Detect environmental adaptation from description"""
        env_keywords = {
            'swamp': ['swamp', 'marsh', 'bog', 'wetland', 'muddy'],
            'volcanic': ['volcano', 'lava', 'magma', 'hellish', 'infernal'],
            'arctic': ['arctic', 'frozen', 'ice', 'snow', 'tundra'],
            'toxic': ['toxic', 'poison', 'acid', 'chemical', 'waste'],
            'desert': ['desert', 'sand', 'arid', 'scorching', 'dune']
        }
        
        for env, keywords in env_keywords.items():
            if any(keyword in description for keyword in keywords):
                return env
        return None
    
    def _detect_damage_level(self, description: str) -> float:
        """Detect battle damage level from description"""
        damage_keywords = {
            0.8: ['heavily damaged', 'nearly destroyed', 'battle-scarred', 'shattered'],
            0.6: ['damaged', 'wounded', 'worn', 'scarred', 'battered'],
            0.4: ['scratched', 'nicked', 'weathered', 'used'],
            0.2: ['slightly worn', 'minor damage', 'scuffed']
        }
        
        for level, keywords in damage_keywords.items():
            if any(keyword in description for keyword in keywords):
                return level
        return 0.0
    
    def _detect_magical_effects(self, description: str) -> Optional[str]:
        """Detect magical enhancement type from description"""
        magic_keywords = {
            'fire': ['fiery', 'burning', 'flaming', 'blazing', 'ignited'],
            'ice': ['icy', 'frozen', 'crystalline', 'glacial', 'frost'],
            'lightning': ['electric', 'lightning', 'shocking', 'charged'],
            'shadow': ['shadowy', 'dark', 'void', 'ethereal', 'ghostly'],
            'holy': ['holy', 'blessed', 'divine', 'radiant', 'pure']
        }
        
        for magic_type, keywords in magic_keywords.items():
            if any(keyword in description for keyword in keywords):
                return magic_type
        return None


class EvolutionaryBreeder:
    """Breed and evolve enemies using genetic algorithms"""
    
    def __init__(self):
        self.rng = random.Random()
    
    def breed_enemies(self, parent1: EnemyBlueprint, parent2: EnemyBlueprint, 
                     seed: Optional[int] = None) -> EnemyBlueprint:
        """Breed two enemies to create offspring with mixed traits"""
        if seed:
            self.rng.seed(seed)
        
        # Mix names
        child_name = f"{parent1.name.split('_')[0]}_{parent2.name.split('_')[-1]}"
        
        # Mix descriptions
        child_description = f"Hybrid of {parent1.description} and {parent2.description}"
        
        # Inherit body type (random choice or mutation)
        if self.rng.random() < 0.1:  # 10% chance of mutation
            body_type = self.rng.choice([EnemyBodyTypes.BLOB, EnemyBodyTypes.QUADRUPED, EnemyBodyTypes.HUMANOID])
        else:
            body_type = self.rng.choice([parent1.body_type, parent2.body_type])
        
        # Choose enemy type based on body type
        enemy_type = parent1.enemy_type if parent1.body_type == body_type else parent2.enemy_type
        
        # Mix materials
        material_theme = self._mix_materials(parent1.material_theme, parent2.material_theme)
        
        # Average size with some variance
        avg_size = (parent1.size_scale + parent2.size_scale) / 2
        size_scale = max(0.3, avg_size + self.rng.uniform(-0.3, 0.3))
        
        # Mix animation sets (prefer more complex)
        animation_set = 'all' if 'all' in [parent1.animation_set, parent2.animation_set] else 'core'
        
        # Breed stats
        child_stats = self._breed_stats(parent1.stats, parent2.stats, size_scale)
        
        return EnemyBlueprint(
            name=child_name,
            description=child_description,
            body_type=body_type,
            enemy_type=enemy_type,
            material_theme=material_theme,
            size_scale=size_scale,
            animation_set=animation_set,
            stats=child_stats,
            generation_seed=seed or self.rng.randint(0, 999999),
            parent_genes=[parent1.name, parent2.name]
        )
    
    def _mix_materials(self, materials1: List[str], materials2: List[str]) -> List[str]:
        """Mix material themes from two parents"""
        # Combine and deduplicate
        combined = list(set(materials1 + materials2))
        
        # Take up to 3 materials
        if len(combined) <= 3:
            return combined
        else:
            return self.rng.sample(combined, 3)
    
    def _breed_stats(self, stats1: EnemyStats, stats2: EnemyStats, size_scale: float) -> EnemyStats:
        """Breed stats from two parents with mutations"""
        
        # Average stats with random variance
        def blend_stat(val1, val2, variance=0.2):
            avg = (val1 + val2) / 2
            mutation = self.rng.uniform(-variance, variance) * avg
            return max(1, int(avg + mutation))
        
        # Breed individual stats
        health = blend_stat(stats1.health, stats2.health)
        damage = blend_stat(stats1.damage, stats2.damage)
        armor = blend_stat(stats1.armor, stats2.armor)
        speed = max(0.1, (stats1.speed + stats2.speed) / 2 + self.rng.uniform(-0.3, 0.3))
        
        # Mix abilities
        combined_abilities = list(set(stats1.special_abilities + stats2.special_abilities))
        abilities = self.rng.sample(combined_abilities, min(4, len(combined_abilities)))
        
        # Mix weaknesses
        combined_weaknesses = list(set(stats1.weaknesses + stats2.weaknesses))
        weaknesses = self.rng.sample(combined_weaknesses, min(3, len(combined_weaknesses)))
        
        # Recalculate threat level
        total_power = health + damage * 2 + armor
        if total_power < 150:
            threat_level = "Low"
        elif total_power < 300:
            threat_level = "Medium"
        elif total_power < 500:
            threat_level = "High"
        else:
            threat_level = "Boss"
        
        return EnemyStats(
            health=health,
            damage=damage,
            speed=speed,
            armor=armor,
            size_modifier=size_scale,
            threat_level=threat_level,
            special_abilities=abilities,
            weaknesses=weaknesses
        )


class DifficultyScaler:
    """Scale enemy stats based on game difficulty"""
    
    DIFFICULTY_MULTIPLIERS = {
        'easy': {'health': 0.7, 'damage': 0.6, 'speed': 0.8},
        'normal': {'health': 1.0, 'damage': 1.0, 'speed': 1.0},
        'hard': {'health': 1.3, 'damage': 1.4, 'speed': 1.2},
        'nightmare': {'health': 2.0, 'damage': 2.0, 'speed': 1.5}
    }
    
    @classmethod
    def scale_enemy(cls, blueprint: EnemyBlueprint, difficulty: str) -> EnemyBlueprint:
        """Scale enemy stats based on difficulty"""
        if difficulty not in cls.DIFFICULTY_MULTIPLIERS:
            return blueprint
        
        multipliers = cls.DIFFICULTY_MULTIPLIERS[difficulty]
        stats = blueprint.stats
        
        # Scale stats
        new_stats = EnemyStats(
            health=int(stats.health * multipliers['health']),
            damage=int(stats.damage * multipliers['damage']),
            speed=stats.speed * multipliers['speed'],
            armor=stats.armor,  # Armor stays the same
            size_modifier=stats.size_modifier,
            threat_level=f"{stats.threat_level} ({difficulty.capitalize()})",
            special_abilities=stats.special_abilities.copy(),
            weaknesses=stats.weaknesses.copy()
        )
        
        # Create new blueprint with scaled stats
        return EnemyBlueprint(
            name=f"{blueprint.name}_{difficulty}",
            description=f"{blueprint.description} (Scaled for {difficulty} difficulty)",
            body_type=blueprint.body_type,
            enemy_type=blueprint.enemy_type,
            material_theme=blueprint.material_theme,
            size_scale=blueprint.size_scale,
            animation_set=blueprint.animation_set,
            stats=new_stats,
            generation_seed=blueprint.generation_seed,
            parent_genes=blueprint.parent_genes
        )


class SmartGenerator:
    """Main smart generation interface"""
    
    def __init__(self):
        self.text_generator = TextToEnemyGenerator()
        self.breeder = EvolutionaryBreeder()
        self.scaler = DifficultyScaler()
    
    def generate_from_text(self, description: str, difficulty: str = 'normal', 
                          seed: Optional[int] = None) -> EnemyBlueprint:
        """Generate enemy from text description with difficulty scaling"""
        blueprint = self.text_generator.generate_from_description(description, seed)
        return self.scaler.scale_enemy(blueprint, difficulty)
    
    def breed_enemies(self, parent1_name: str, parent2_name: str, 
                     difficulty: str = 'normal', seed: Optional[int] = None) -> EnemyBlueprint:
        """Breed two enemies (placeholder - would need enemy storage)"""
        # This would need a database/storage system to work fully
        # For now, return a sample
        pass
    
    def export_stats(self, blueprint: EnemyBlueprint, format: str = 'json') -> str:
        """Export enemy stats for game integration"""
        if format == 'json':
            return json.dumps(blueprint.stats.to_dict(), indent=2)
        elif format == 'godot':
            return self._export_godot_format(blueprint)
        elif format == 'unity':
            return self._export_unity_format(blueprint)
        else:
            return str(blueprint.stats.to_dict())
    
    def _export_godot_format(self, blueprint: EnemyBlueprint) -> str:
        """Export in Godot-friendly format"""
        stats = blueprint.stats
        return f"""# {blueprint.name} Enemy Stats
extends Resource
class_name {blueprint.name}Stats

export var health: int = {stats.health}
export var damage: int = {stats.damage}
export var speed: float = {stats.speed:.2f}
export var armor: int = {stats.armor}
export var size_modifier: float = {stats.size_modifier:.2f}
export var threat_level: String = "{stats.threat_level}"
export var special_abilities: PoolStringArray = {stats.special_abilities}
export var weaknesses: PoolStringArray = {stats.weaknesses}
"""
    
    def _export_unity_format(self, blueprint: EnemyBlueprint) -> str:
        """Export in Unity C# format"""
        stats = blueprint.stats
        abilities_str = ', '.join([f'"{a}"' for a in stats.special_abilities])
        weaknesses_str = ', '.join([f'"{w}"' for w in stats.weaknesses])
        
        return f"""// {blueprint.name} Enemy Stats
[System.Serializable]
public class {blueprint.name}Stats : EnemyStats
{{
    public int health = {stats.health};
    public int damage = {stats.damage};
    public float speed = {stats.speed:.2f}f;
    public int armor = {stats.armor};
    public float sizeModifier = {stats.size_modifier:.2f}f;
    public string threatLevel = "{stats.threat_level}";
    public string[] specialAbilities = {{ {abilities_str} }};
    public string[] weaknesses = {{ {weaknesses_str} }};
}}
"""