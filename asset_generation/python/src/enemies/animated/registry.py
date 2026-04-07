"""
Central registry for animated enemy types: builder and class map (aligned with ANIMATED_SLUGS).
"""

from __future__ import annotations

from ...core.rig_types import AnimatedBuildResult
from ...utils.enemy_slug_registry import ANIMATED_SLUGS
from ..animated_carapace_husk import AnimatedCarapaceHusk
from ..animated_claw_crawler import AnimatedClawCrawler
from ..animated_imp import AnimatedImp
from ..animated_slug import AnimatedSlug
from ..animated_spider import AnimatedSpider
from ..animated_spitter import AnimatedSpitter

_ANIMATED_ENEMY_CLASSES: tuple[tuple[str, type], ...] = (
    ("spider", AnimatedSpider),
    ("slug", AnimatedSlug),
    ("imp", AnimatedImp),
    ("spitter", AnimatedSpitter),
    ("claw_crawler", AnimatedClawCrawler),
    ("carapace_husk", AnimatedCarapaceHusk),
)

ENEMY_CLASSES: dict[str, type] = dict(_ANIMATED_ENEMY_CLASSES)

if tuple(ENEMY_CLASSES.keys()) != ANIMATED_SLUGS:
    raise RuntimeError(
        "Animated enemy registry order/keys must match utils.enemy_slug_registry.ANIMATED_SLUGS exactly; "
        f"got {tuple(ENEMY_CLASSES.keys())!r} vs {ANIMATED_SLUGS!r}"
    )
if set(ENEMY_CLASSES.keys()) != set(ANIMATED_SLUGS):
    raise RuntimeError("Animated enemy registry keys must equal ANIMATED_SLUGS set")


class AnimatedEnemyBuilder:
    """Factory for creating animated enemies."""

    ENEMY_CLASSES = ENEMY_CLASSES

    @classmethod
    def create_enemy(
        cls,
        enemy_type: str,
        materials,
        rng,
        prefab_mesh=None,
        build_options: dict | None = None,
    ) -> AnimatedBuildResult:
        """Build one animated enemy; returns typed result."""
        if enemy_type not in cls.ENEMY_CLASSES:
            raise ValueError(f"Unknown enemy type: {enemy_type}")

        enemy_class = cls.ENEMY_CLASSES[enemy_type]
        enemy = enemy_class(enemy_type, materials, rng, build_options=build_options)
        build_result = enemy.build(prefab_mesh=prefab_mesh)
        attack_profile = enemy.get_attack_profile()

        if isinstance(build_result, tuple):
            armature, mesh = build_result
            return AnimatedBuildResult(armature=armature, mesh=mesh, attack_profile=attack_profile)

        return AnimatedBuildResult(armature=None, mesh=build_result, attack_profile=attack_profile)

    @classmethod
    def get_available_types(cls) -> list[str]:
        return list(ANIMATED_SLUGS)
