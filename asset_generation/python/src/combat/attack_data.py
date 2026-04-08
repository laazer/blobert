"""
Attack data structures for the enemy combat system
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class AttackType(Enum):
    """Elemental and physical damage categories"""
    PHYSICAL = "physical"
    FIRE = "fire"
    ICE = "ice"
    ACID = "acid"
    POISON = "poison"


@dataclass
class AttackData:
    """Defines one attack: combat statistics plus which animation it drives"""

    name: str
    animation_name: str       # Matches an AnimationTypes constant
    attack_type: AttackType
    damage_min: float
    damage_max: float
    range: float              # World units
    hit_frame: int            # Frame in the animation when damage registers
    cooldown_seconds: float
    knockback_force: float
    is_area_of_effect: bool = False
    aoe_radius: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "animation_name": self.animation_name,
            "attack_type": self.attack_type.value,
            "damage_min": self.damage_min,
            "damage_max": self.damage_max,
            "range": self.range,
            "hit_frame": self.hit_frame,
            "cooldown_seconds": self.cooldown_seconds,
            "knockback_force": self.knockback_force,
            "is_area_of_effect": self.is_area_of_effect,
            "aoe_radius": self.aoe_radius,
        }
