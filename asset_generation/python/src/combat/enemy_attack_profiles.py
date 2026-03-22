"""
Attack profiles for each enemy type.

Each profile is a list of AttackData instances — one per distinct attack.
The hit_frame values are derived from AnimationConfig so they stay in sync
with any future timing changes.
"""

from typing import Dict, List

from .attack_data import AttackData, AttackType
from ..utils.constants import AnimationConfig, AnimationTypes


def _hit_frame(animation_name: str, fraction: float) -> int:
    """Return the frame at which damage registers, as a fraction of animation length."""
    return int(AnimationConfig.get_length(animation_name) * fraction)


ADHESION_BUG_ATTACKS: List[AttackData] = [
    AttackData(
        name="pounce",
        animation_name=AnimationTypes.ATTACK,
        attack_type=AttackType.PHYSICAL,
        damage_min=5.0,
        damage_max=15.0,
        range=3.0,
        hit_frame=_hit_frame(AnimationTypes.ATTACK, 0.5),   # mid-leap
        cooldown_seconds=2.0,
        knockback_force=5.0,
    ),
    AttackData(
        name="acid_bite",
        animation_name=AnimationTypes.SPECIAL_ATTACK,
        attack_type=AttackType.ACID,
        damage_min=12.0,
        damage_max=28.0,
        range=1.5,
        hit_frame=_hit_frame(AnimationTypes.SPECIAL_ATTACK, 2 / 3),  # after slam
        cooldown_seconds=5.0,
        knockback_force=2.0,
    ),
]

TAR_SLUG_ATTACKS: List[AttackData] = [
    AttackData(
        name="tar_expansion",
        animation_name=AnimationTypes.ATTACK,
        attack_type=AttackType.ACID,
        damage_min=3.0,
        damage_max=8.0,
        range=4.0,
        hit_frame=_hit_frame(AnimationTypes.ATTACK, 2 / 3),   # expansion peak
        cooldown_seconds=3.0,
        knockback_force=1.0,
        is_area_of_effect=True,
        aoe_radius=4.0,
    ),
    AttackData(
        name="acid_slam",
        animation_name=AnimationTypes.SPECIAL_ATTACK,
        attack_type=AttackType.POISON,
        damage_min=15.0,
        damage_max=30.0,
        range=5.0,
        hit_frame=_hit_frame(AnimationTypes.SPECIAL_ATTACK, 0.5),  # slam impact
        cooldown_seconds=6.0,
        knockback_force=4.0,
        is_area_of_effect=True,
        aoe_radius=5.0,
    ),
]

EMBER_IMP_ATTACKS: List[AttackData] = [
    AttackData(
        name="fire_punch",
        animation_name=AnimationTypes.ATTACK,
        attack_type=AttackType.FIRE,
        damage_min=8.0,
        damage_max=15.0,
        range=1.5,
        hit_frame=_hit_frame(AnimationTypes.ATTACK, 0.5),   # arm fully extended
        cooldown_seconds=1.5,
        knockback_force=4.0,
    ),
    AttackData(
        name="inferno_slam",
        animation_name=AnimationTypes.SPECIAL_ATTACK,
        attack_type=AttackType.FIRE,
        damage_min=20.0,
        damage_max=38.0,
        range=2.5,
        hit_frame=_hit_frame(AnimationTypes.SPECIAL_ATTACK, 2 / 3),  # arms crash down
        cooldown_seconds=6.0,
        knockback_force=8.0,
        is_area_of_effect=True,
        aoe_radius=2.5,
    ),
]

_ATTACK_PROFILES: Dict[str, List[AttackData]] = {
    'adhesion_bug': ADHESION_BUG_ATTACKS,
    'tar_slug': TAR_SLUG_ATTACKS,
    'ember_imp': EMBER_IMP_ATTACKS,
}


def get_attack_profile(enemy_type: str) -> List[AttackData]:
    """Return the attack list for the given enemy type, or [] if unknown."""
    return _ATTACK_PROFILES.get(enemy_type, [])
