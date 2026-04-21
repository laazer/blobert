"""Migration helpers for legacy registry formats and default manifest seed."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from src.utils.config import ANIMATED_SLUGS
except ImportError:
    from utils.config import ANIMATED_SLUGS  # type: ignore[import-not-found]

SCHEMA_VERSION = 1
_DEFAULT_VARIANT_INDEX = 0


def _default_version_id_for_slug(slug: str) -> str:
    return f"{slug}_animated_{_DEFAULT_VARIANT_INDEX:02d}"


def _default_path_for_slug(slug: str) -> str:
    return f"animated_exports/{_default_version_id_for_slug(slug)}.glb"


def default_migrated_manifest() -> dict[str, Any]:
    enemies: dict[str, Any] = {}
    for slug in ANIMATED_SLUGS:
        vid = _default_version_id_for_slug(slug)
        enemies[slug] = {
            "versions": [
                {
                    "id": vid,
                    "path": _default_path_for_slug(slug),
                    "draft": False,
                    "in_use": True,
                }
            ]
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "enemies": enemies,
        "player": {"versions": [], "slots": []},
        "player_active_visual": None,
    }


def _legacy_pav_to_player_block(pav: dict[str, Any]) -> dict[str, Any]:
    pp = pav["path"]
    pd = bool(pav["draft"])
    name = Path(pp).name
    stem = name[:-4] if name.lower().endswith(".glb") else Path(pp).stem
    if not stem or not stem.strip():
        stem = "player_registry_00"
    vid = stem
    in_use = not pd
    row: dict[str, Any] = {"id": vid, "path": pp, "draft": pd, "in_use": in_use}
    slots: list[str] = [vid] if not pd else []
    return {"versions": [row], "slots": slots}


def _derive_player_active_visual_from_block(player_block: dict[str, Any]) -> dict[str, Any] | None:
    slots = player_block.get("slots")
    if not isinstance(slots, list) or len(slots) == 0:
        return None
    versions = player_block.get("versions", [])
    for vid0 in slots:
        if not isinstance(vid0, str) or vid0 == "":
            continue
        row = next((r for r in versions if r.get("id") == vid0), None)
        if row is None:
            continue
        return {"path": row["path"], "draft": bool(row.get("draft"))}
    return None
