"""
Data structures for level objects: trap definitions and per-object metadata
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class TrapType(Enum):
    SPIKE = "spike"
    FIRE = "fire"
    ICE = "ice"
    CRUSHER = "crusher"


@dataclass
class TrapData:
    """Combat data for a single trap attack, mirroring AttackData for enemies."""

    name: str
    trap_type: TrapType
    damage_per_hit: float
    trigger_radius: float
    cooldown_seconds: float
    activation_delay_seconds: float = 0.0
    is_visible_when_inactive: bool = True

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "trap_type": self.trap_type.value,
            "damage_per_hit": self.damage_per_hit,
            "trigger_radius": self.trigger_radius,
            "cooldown_seconds": self.cooldown_seconds,
            "activation_delay_seconds": self.activation_delay_seconds,
            "is_visible_when_inactive": self.is_visible_when_inactive,
        }
