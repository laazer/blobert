"""
Load / validate / persist ``model_registry.json`` (MRVC).

Consumer: ``spawn_eligible_paths`` implements MRVC-4 default pool filtering
(non-draft and in-use only).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

# Dual entry: pytest imports ``src.model_registry``; FastAPI adds ``python/src`` only.
try:
    from utils.enemy_slug_registry import ANIMATED_SLUGS
except ImportError:
    from src.utils.enemy_slug_registry import ANIMATED_SLUGS

SCHEMA_VERSION = 1

ALLOWLIST_PREFIXES: tuple[str, ...] = (
    "animated_exports/",
    "exports/",
    "player_exports/",
    "level_exports/",
)

REGISTRY_FILENAME = "model_registry.json"

# Default variant index for MRVC-7 migration (matches editor ``glbVariants`` stem ``*_00``).
_DEFAULT_VARIANT_INDEX = 0


def registry_path(python_root: Path) -> Path:
    return python_root / REGISTRY_FILENAME


def _path_is_allowlisted(path: str) -> bool:
    if not path or path.startswith("/") or ".." in path.split("/"):
        return False
    return any(path.startswith(p) for p in ALLOWLIST_PREFIXES)


def _default_version_id_for_slug(slug: str) -> str:
    stem = f"{slug}_animated_{_DEFAULT_VARIANT_INDEX:02d}"
    return stem


def _default_path_for_slug(slug: str) -> str:
    stem = _default_version_id_for_slug(slug)
    return f"animated_exports/{stem}.glb"


def default_migrated_manifest() -> dict[str, Any]:
    """MRVC-7 single-version migration shape (in-memory; not written until a save)."""
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
        "player_active_visual": None,
    }


def validate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate MRVC-1 / MRVC-2 / MRVC-3 / MRVC-8. Normalizes invalid draft+in_use for enemies.
    Returns a deep-ish normalized copy suitable for JSON round-trip.
    """
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")

    extra_top = set(data.keys()) - {"schema_version", "enemies", "player_active_visual"}
    if extra_top:
        raise ValueError(f"unexpected top-level keys: {sorted(extra_top)}")

    sv = data.get("schema_version")
    if sv != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {sv!r}")

    enemies_raw = data.get("enemies")
    if not isinstance(enemies_raw, dict):
        raise ValueError("enemies must be an object")

    enemies_out: dict[str, Any] = {}
    for family, fam_val in enemies_raw.items():
        if not isinstance(family, str) or not family.strip():
            raise ValueError("enemy family keys must be non-empty strings")
        if not isinstance(fam_val, dict):
            raise ValueError(f"enemies[{family!r}] must be an object")
        versions_raw = fam_val.get("versions")
        if not isinstance(versions_raw, list):
            raise ValueError(f"enemies[{family!r}].versions must be an array")

        seen_ids: set[str] = set()
        versions_out: list[dict[str, Any]] = []
        for i, row in enumerate(versions_raw):
            if not isinstance(row, dict):
                raise ValueError(f"enemies[{family!r}].versions[{i}] must be an object")
            for k in ("id", "path", "draft", "in_use"):
                if k not in row:
                    raise ValueError(f"enemies[{family!r}].versions[{i}] missing {k!r}")
            vid = row["id"]
            path = row["path"]
            draft = row["draft"]
            in_use = row["in_use"]
            if not isinstance(vid, str) or not vid.strip():
                raise ValueError(f"enemies[{family!r}].versions[{i}].id invalid")
            if vid in seen_ids:
                raise ValueError(f"duplicate version id {vid!r} in family {family!r}")
            seen_ids.add(vid)
            if not isinstance(path, str) or not _path_is_allowlisted(path):
                raise ValueError(f"invalid path for {family!r} / {vid!r}: {path!r}")
            if not isinstance(draft, bool) or not isinstance(in_use, bool):
                raise ValueError(f"draft/in_use must be booleans for {family!r} / {vid!r}")
            use = in_use
            if draft and in_use:
                use = False
            versions_out.append(
                {"id": vid, "path": path, "draft": draft, "in_use": use},
            )

        enemies_out[family] = {"versions": versions_out}

    player_out: dict[str, Any] | None
    pav = data.get("player_active_visual")
    if pav is None:
        player_out = None
    elif isinstance(pav, dict):
        if set(pav.keys()) != {"path", "draft"}:
            raise ValueError("player_active_visual must have only path and draft")
        pp = pav["path"]
        pd = pav["draft"]
        if not isinstance(pp, str) or not _path_is_allowlisted(pp):
            raise ValueError(f"invalid player_active_visual.path: {pp!r}")
        if not isinstance(pd, bool):
            raise ValueError("player_active_visual.draft must be boolean")
        player_out = {"path": pp, "draft": pd}
    else:
        raise ValueError("player_active_visual must be null or an object")

    return {
        "schema_version": SCHEMA_VERSION,
        "enemies": enemies_out,
        "player_active_visual": player_out,
    }


def load_effective_manifest(python_root: Path) -> dict[str, Any]:
    """Read ``model_registry.json`` or return the MRVC-7 default (not persisted)."""
    path = registry_path(python_root)
    if not path.is_file():
        return default_migrated_manifest()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ValueError("registry file must contain a JSON object")
    return validate_manifest(raw)


def save_manifest_atomic(python_root: Path, data: dict[str, Any]) -> None:
    """Write validated manifest to ``python_root/model_registry.json``."""
    validated = validate_manifest(data)
    path = registry_path(python_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(validated, indent=2, sort_keys=True) + "\n"
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_model_registry_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def patch_enemy_version(
    python_root: Path,
    family: str,
    version_id: str,
    *,
    draft: bool | None = None,
    in_use: bool | None = None,
) -> dict[str, Any]:
    """Update flags for one enemy version; persists on success."""
    if draft is None and in_use is None:
        raise ValueError("at least one of draft or in_use must be set")

    data = load_effective_manifest(python_root)
    fam = data["enemies"].get(family)
    if fam is None:
        raise KeyError(f"unknown family: {family}")
    versions: list[dict[str, Any]] = fam["versions"]
    found = next((v for v in versions if v["id"] == version_id), None)
    if found is None:
        raise KeyError(f"unknown version {version_id!r} for family {family!r}")

    if draft is not None:
        found["draft"] = draft
    if in_use is not None:
        found["in_use"] = in_use

    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return validated


def patch_player_active_visual(
    python_root: Path,
    *,
    draft: bool | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Update player active visual flags (MRVC-2). Persists on success."""
    if draft is None and path is None:
        raise ValueError("at least one of draft or path must be set")

    data = load_effective_manifest(python_root)
    pav = data.get("player_active_visual")
    if pav is None:
        raise KeyError("player_active_visual is null; set an active path before toggling draft")

    next_pav = dict(pav)
    if path is not None:
        if not _path_is_allowlisted(path):
            raise ValueError(f"invalid player path: {path!r}")
        next_pav["path"] = path
    if draft is not None:
        next_pav["draft"] = draft

    data["player_active_visual"] = next_pav
    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return validated


def spawn_eligible_paths(manifest: dict[str, Any], family: str) -> list[str]:
    """
    MRVC-4 default pool: ``draft == false`` and ``in_use == true`` and valid path.
    """
    fam = manifest.get("enemies", {}).get(family)
    if not fam:
        return []
    out: list[str] = []
    for row in fam.get("versions", []):
        if row.get("draft") is False and row.get("in_use") is True:
            p = row.get("path")
            if isinstance(p, str) and _path_is_allowlisted(p):
                out.append(p)
    return out
