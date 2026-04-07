"""Text keywords per body family — no Blender/rig imports (safe for smart_generation)."""

from __future__ import annotations

from typing import Dict, List

from .ids import EnemyBodyTypes

_BLOB: tuple[str, ...] = ("blob", "slime", "ooze", "jelly", "goo", "puddle", "liquid")
_QUADRUPED: tuple[str, ...] = ("spider", "bug", "insect", "crawler", "legged", "scuttling")
_HUMANOID: tuple[str, ...] = ("humanoid", "warrior", "soldier", "biped", "person", "figure")


def get_body_type_keywords() -> Dict[str, List[str]]:
    """Keywords per body type id (includes SLIME → same list as BLOB)."""
    out: Dict[str, List[str]] = {
        EnemyBodyTypes.BLOB: list(_BLOB),
        EnemyBodyTypes.QUADRUPED: list(_QUADRUPED),
        EnemyBodyTypes.HUMANOID: list(_HUMANOID),
    }
    out[EnemyBodyTypes.SLIME] = list(_BLOB)
    return out


def keywords_for_family(body_id: str) -> List[str]:
    """Keyword list for a canonical family id (blob / quadruped / humanoid)."""
    bt = (body_id or "").strip().lower()
    if bt == EnemyBodyTypes.BLOB:
        return list(_BLOB)
    if bt == EnemyBodyTypes.HUMANOID:
        return list(_HUMANOID)
    return list(_QUADRUPED)
