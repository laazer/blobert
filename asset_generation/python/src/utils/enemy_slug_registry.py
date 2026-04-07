"""
Canonical enemy slug sequences for CLI and generation.

Must not import utils.constants (or any module that loads constants) to avoid cycles.
"""

ANIMATED_SLUGS: tuple[str, ...] = (
    "spider",
    "slug",
    "imp",
    "spitter",
    "claw_crawler",
    "carapace_husk",
)

# Human-readable names for UI (asset editor / GET /api/meta/enemies). Keys must match ANIMATED_SLUGS.
ANIMATED_ENEMY_LABELS: dict[str, str] = {
    "spider": "Spider",
    "slug": "Slug",
    "imp": "Imp",
    "spitter": "Spitter",
    "claw_crawler": "Claw crawler",
    "carapace_husk": "Carapace husk",
}

if set(ANIMATED_ENEMY_LABELS.keys()) != set(ANIMATED_SLUGS):
    raise RuntimeError("ANIMATED_ENEMY_LABELS keys must match ANIMATED_SLUGS exactly")


def animated_enemies_for_api() -> list[dict[str, str]]:
    """[{slug, label}, ...] in ANIMATED_SLUGS order for HTTP clients."""
    return [{"slug": s, "label": ANIMATED_ENEMY_LABELS[s]} for s in ANIMATED_SLUGS]


STATIC_SLUGS: tuple[str, ...] = (
    "glue_drone",
    "melt_worm",
    "frost_jelly",
    "stone_burrower",
    "ferro_drone",
)
