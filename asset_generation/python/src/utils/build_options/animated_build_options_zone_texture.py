"""Per-zone ``texture_*`` control defs expanded to ``feat_{zone}_texture_*`` for the asset editor."""

from __future__ import annotations

from typing import Any

from .animated_build_options_appendage_defs import _texture_control_defs

_ZONE_LABEL = {
    "body": "Body",
    "head": "Head",
    "limbs": "Limbs",
    "joints": "Joints",
    "extra": "Extra",
}


def zone_texture_control_defs(zones: tuple[str, ...]) -> list[dict[str, Any]]:
    """Per-zone surface texture controls; keys ``feat_{zone}_texture_*`` (aligned with material zones)."""
    base = _texture_control_defs()
    out: list[dict[str, Any]] = []
    for z in zones:
        zlab = _ZONE_LABEL.get(z, z.replace("_", " ").title())
        for c in base:
            old_key = str(c["key"])
            if not old_key.startswith("texture_"):
                continue
            suffix = old_key.removeprefix("texture_")
            new_key = f"feat_{z}_texture_{suffix}"
            label = f"{zlab} — {c['label']}"
            out.append({**c, "key": new_key, "label": label})
    return out
