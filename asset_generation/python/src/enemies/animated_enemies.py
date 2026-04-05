"""
Animated enemy builders with enhanced materials and animations
"""

from .animated_acid_spitter import AnimatedAcidSpitter
from .animated_adhesion_bug import AnimatedAdhesionBug
from .animated_carapace_husk import AnimatedCarapaceHusk
from .animated_claw_crawler import AnimatedClawCrawler
from .animated_ember_imp import AnimatedEmberImp
from .animated_tar_slug import AnimatedTarSlug


class AnimatedEnemyBuilder:
    """Factory for creating animated enemies"""

    ENEMY_CLASSES = {
        'adhesion_bug': AnimatedAdhesionBug,
        'tar_slug': AnimatedTarSlug,
        'ember_imp': AnimatedEmberImp,
        'acid_spitter': AnimatedAcidSpitter,
        'claw_crawler': AnimatedClawCrawler,
        'carapace_husk': AnimatedCarapaceHusk,
    }

    @classmethod
    def create_enemy(cls, enemy_type, materials, rng, prefab_mesh=None):
        """Create an animated enemy and return (armature, mesh, attack_profile).

        Args:
            enemy_type: Registered enemy type string.
            materials: Material system dict from setup_materials().
            rng: Random number generator for procedural variation.
            prefab_mesh: Optional pre-imported mesh to use instead of
                procedural geometry (see src/prefabs/prefab_loader.py).
        """
        if enemy_type not in cls.ENEMY_CLASSES:
            raise ValueError(f"Unknown enemy type: {enemy_type}")

        enemy_class = cls.ENEMY_CLASSES[enemy_type]
        enemy = enemy_class(enemy_type, materials, rng)
        build_result = enemy.build(prefab_mesh=prefab_mesh)
        attack_profile = enemy.get_attack_profile()

        if isinstance(build_result, tuple):
            armature, mesh = build_result
            return armature, mesh, attack_profile

        return build_result, None, attack_profile

    @classmethod
    def get_available_types(cls):
        """Get list of available animated enemy types"""
        return list(cls.ENEMY_CLASSES.keys())
