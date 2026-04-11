"""Per-limb / per-joint feature control defs (extracted for module size limits)."""

from __future__ import annotations

from typing import Any

from .blender_stubs import ensure_blender_stubs


def _part_feature_control_defs(slug: str) -> list[dict[str, Any]]:
    """Optional per-limb / per-joint material keys (flat API); merged into ``features[*].parts``."""
    from .animated_build_options import _FINISH_OPTIONS_ORDER

    ensure_blender_stubs()
    try:
        from enemies.animated.registry import AnimatedEnemyBuilder
    except ImportError:
        from src.enemies.animated.registry import AnimatedEnemyBuilder

    cls = AnimatedEnemyBuilder.ENEMY_CLASSES.get(slug)
    if cls is None:
        return []
    defs: list[dict[str, Any]] = []
    if slug in ("imp", "carapace_husk"):
        n_arm = max(1, min(8, int(getattr(cls, "ARM_SEGMENTS", 1))))
        n_leg = max(1, min(8, int(getattr(cls, "LEG_SEGMENTS", 1))))
        jvis = bool(getattr(cls, "LIMB_JOINT_VISUAL", False))
        for label_base, idx_prefix, n_seg in (
            ("Arm", "arm", n_arm),
            ("Leg", "leg", n_leg),
        ):
            for side in range(2):
                pid = f"{idx_prefix}_{side}"
                defs.append(
                    {
                        "key": f"feat_limb_{pid}_finish",
                        "label": f"{label_base} {side} (limb) finish",
                        "type": "select_str",
                        "options": list(_FINISH_OPTIONS_ORDER),
                        "default": "default",
                    }
                )
                defs.append(
                    {
                        "key": f"feat_limb_{pid}_hex",
                        "label": f"{label_base} {side} (limb) hex",
                        "type": "str",
                        "default": "",
                    }
                )
                if jvis:
                    for ji in range(max(0, n_seg - 1)):
                        jpid = f"{idx_prefix}_{side}_j{ji}"
                        defs.append(
                            {
                                "key": f"feat_joint_{jpid}_finish",
                                "label": f"{label_base} {side} joint {ji} finish",
                                "type": "select_str",
                                "options": list(_FINISH_OPTIONS_ORDER),
                                "default": "default",
                            }
                        )
                        defs.append(
                            {
                                "key": f"feat_joint_{jpid}_hex",
                                "label": f"{label_base} {side} joint {ji} hex",
                                "type": "str",
                                "default": "",
                            }
                        )
    if slug == "spider":
        for leg in range(8):
            pid = f"leg_{leg}"
            defs.append(
                {
                    "key": f"feat_limb_{pid}_finish",
                    "label": f"Leg {leg} cylinders finish",
                    "type": "select_str",
                    "options": list(_FINISH_OPTIONS_ORDER),
                    "default": "default",
                }
            )
            defs.append(
                {
                    "key": f"feat_limb_{pid}_hex",
                    "label": f"Leg {leg} cylinders hex",
                    "type": "str",
                    "default": "",
                }
            )
            for jn in ("root", "knee", "ankle", "foot"):
                jpid = f"leg_{leg}_{jn}"
                defs.append(
                    {
                        "key": f"feat_joint_{jpid}_finish",
                        "label": f"Leg {leg} joint ({jn}) finish",
                        "type": "select_str",
                        "options": list(_FINISH_OPTIONS_ORDER),
                        "default": "default",
                    }
                )
                defs.append(
                    {
                        "key": f"feat_joint_{jpid}_hex",
                        "label": f"Leg {leg} joint ({jn}) hex",
                        "type": "str",
                        "default": "",
                    }
                )
    return defs
