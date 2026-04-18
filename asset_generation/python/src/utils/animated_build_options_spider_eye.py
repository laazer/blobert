"""Spider eye_count / placement controls for GET /api/meta (single source: ``AnimatedSpider``)."""

from __future__ import annotations

from typing import Any

from .blender_stubs import ensure_blender_stubs


def placement_seed_def(placement_seed_max: int) -> dict[str, Any]:
    return {
        "key": "placement_seed",
        "label": "Placement seed (random distribution)",
        "type": "int",
        "min": 0,
        "max": placement_seed_max,
        "default": 0,
    }


def spider_eye_control_defs(
    *,
    placement_clustering_min: float,
    placement_clustering_max: float,
    default_placement_clustering: float,
    distribution_modes: tuple[str, ...],
    default_distribution: str,
) -> list[dict[str, Any]]:
    ensure_blender_stubs()
    try:
        from enemies.animated_spider import AnimatedSpider
    except ImportError:
        from src.enemies.animated_spider import AnimatedSpider

    return [
        {
            "key": "eye_count",
            "label": "Eyes",
            "type": "select",
            "options": list(AnimatedSpider.ALLOWED_EYE_COUNTS),
            "default": AnimatedSpider.DEFAULT_EYE_COUNT,
        },
        {
            "key": "eye_distribution",
            "label": "Eye placement",
            "type": "select_str",
            "options": list(distribution_modes),
            "default": default_distribution,
            "segmented": True,
        },
        {
            "key": "eye_uniform_shape",
            "label": "Eye uniform pattern",
            "type": "select_str",
            "options": ["arc"],
            "default": "arc",
        },
        {
            "key": "eye_clustering",
            "label": "Eye clustering (multi-eye)",
            "type": "float",
            "min": placement_clustering_min,
            "max": placement_clustering_max,
            "step": 0.05,
            "default": default_placement_clustering,
            "unit": "0–1",
            "hint": "How tightly grouped vs spread eyes are when placement is random (multi-eye only).",
        },
    ]
