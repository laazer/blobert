"""Registry read/query helpers for the FastAPI layer.

These functions intentionally live outside `routers/registry.py` so the router can stay
transport-only (request parsing/HTTP mapping) while still sharing the same behavior.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from services.python_bridge import import_asset_module


def load_registry_json_unvalidated(python_root: Path) -> dict[str, Any]:
    registry_file = python_root / "model_registry.json"
    if not registry_file.is_file():
        reg = _load_model_registry_service()
        return reg.default_migrated_manifest()
    try:
        data = json.loads(registry_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError("invalid registry JSON") from e
    if not isinstance(data, dict):
        raise ValueError("registry payload must be an object")
    return data


def normalize_registry_relative_glb_path_for_http(path: str) -> str:
    reg = _load_model_registry_service()
    try:
        return reg.normalize_registry_relative_glb_path(path)
    except ValueError as e:
        detail = str(e)
        if detail.startswith("forbidden target path class:"):
            raise HTTPException(status_code=403, detail=detail) from e
        raise


def safe_is_file_under_python_root(python_root: Path, rel_path: str) -> bool:
    try:
        return (python_root / rel_path).is_file()
    except OSError:
        return False


def player_export_rows_for_load_existing(data: dict[str, Any]) -> list[dict[str, str]]:
    """Registry-backed player rows (draft or in-use), same eligibility as enemy versions."""
    out: list[dict[str, str]] = []
    player_block = data.get("player")
    pav = data.get("player_active_visual")
    use_legacy_pav = False
    if isinstance(player_block, dict):
        versions = player_block.get("versions")
        if isinstance(versions, list) and len(versions) > 0:
            for row in versions:
                if not isinstance(row, dict):
                    continue
                version_id = row.get("id")
                path = row.get("path")
                draft = row.get("draft")
                in_use = row.get("in_use")
                if not isinstance(version_id, str) or not isinstance(path, str):
                    continue
                if draft is not True and in_use is not True:
                    continue
                try:
                    canonical = normalize_registry_relative_glb_path_for_http(path)
                except (HTTPException, ValueError):
                    continue
                out.append({"kind": "player", "version_id": version_id, "path": canonical})
        elif isinstance(pav, dict):
            use_legacy_pav = True
    elif isinstance(pav, dict):
        use_legacy_pav = True

    if use_legacy_pav and isinstance(pav, dict):
        ppath = pav.get("path")
        pdraft = pav.get("draft")
        if isinstance(ppath, str) and isinstance(pdraft, bool):
            try:
                canonical = normalize_registry_relative_glb_path_for_http(ppath)
            except (HTTPException, ValueError):
                return out
            name = Path(ppath).name
            stem = name[:-4] if name.lower().endswith(".glb") else Path(ppath).stem
            vid = stem.strip() or "player_registry_00"
            out.append({"kind": "player", "version_id": vid, "path": canonical})
    return out


def load_existing_candidates_from_registry(python_root: Path) -> list[dict[str, str]]:
    data = load_registry_json_unvalidated(python_root)
    enemies = data.get("enemies")
    rows: list[dict[str, str]] = []

    if isinstance(enemies, dict):
        for family, family_data in enemies.items():
            if not isinstance(family, str):
                continue
            versions = family_data.get("versions") if isinstance(family_data, dict) else None
            if not isinstance(versions, list):
                continue
            for row in versions:
                if not isinstance(row, dict):
                    continue
                version_id = row.get("id")
                path = row.get("path")
                draft = row.get("draft")
                in_use = row.get("in_use")
                if not isinstance(version_id, str) or not isinstance(path, str):
                    continue
                if draft is not True and in_use is not True:
                    continue
                try:
                    canonical = normalize_registry_relative_glb_path_for_http(path)
                except (HTTPException, ValueError):
                    continue
                rows.append(
                    {
                        "kind": "enemy",
                        "family": family,
                        "version_id": version_id,
                        "path": canonical,
                    },
                )

    rows.sort(key=lambda row: (row["family"], row["version_id"]))
    player_rows = player_export_rows_for_load_existing(data)
    player_rows.sort(key=lambda row: row["version_id"])
    return rows + player_rows


def resolve_enemy_identity_path(
    python_root: Path,
    family: str,
    version_id: str,
) -> str:
    for row in load_existing_candidates_from_registry(python_root):
        if row.get("kind") != "enemy":
            continue
        if row.get("family") == family and row.get("version_id") == version_id:
            return row["path"]
    raise KeyError(f"unknown version {version_id!r} for family {family!r}")


def resolve_player_identity_path(python_root: Path, version_id: str) -> str:
    for row in load_existing_candidates_from_registry(python_root):
        if row.get("kind") != "player":
            continue
        if row.get("version_id") == version_id:
            return row["path"]
    raise KeyError(f"unknown player version id {version_id!r}")


def _load_model_registry_service():
    return import_asset_module("src.model_registry.service")
