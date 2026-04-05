"""
Canonical enemy slug sequences for CLI and generation.

Must not import utils.constants (or any module that loads constants) to avoid cycles.
"""

ANIMATED_SLUGS: tuple[str, ...] = (
    "adhesion_bug",
    "tar_slug",
    "ember_imp",
    "acid_spitter",
    "claw_crawler",
    "carapace_husk",
)

STATIC_SLUGS: tuple[str, ...] = (
    "glue_drone",
    "melt_worm",
    "frost_jelly",
    "stone_burrower",
    "ferro_drone",
)
