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

# Optional human-readable label in ``enemies[*].versions[*].name`` (editor / tooling).
_MAX_VERSION_NAME_LEN = 128

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
        "player": {"versions": [], "slots": []},
        "player_active_visual": None,
    }


def _legacy_pav_to_player_block(pav: dict[str, Any]) -> dict[str, Any]:
    """Build a ``player`` family dict from legacy ``player_active_visual`` only."""
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
    """Legacy single-path view: first assigned slot row, or ``None`` when none."""
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


def _normalize_registry_family_block(context: str, fam_val: Any) -> dict[str, Any]:
    """Validate ``versions`` + optional ``slots`` (same rules as one enemy family)."""
    if not isinstance(fam_val, dict):
        raise ValueError(f"{context} must be an object")
    extra_family = set(fam_val.keys()) - {"versions", "slots"}
    if extra_family:
        raise ValueError(f"unexpected keys for {context}: {sorted(extra_family)}")
    versions_raw = fam_val.get("versions")
    if not isinstance(versions_raw, list):
        raise ValueError(f"{context}.versions must be an array")

    seen_ids: set[str] = set()
    versions_out: list[dict[str, Any]] = []
    for i, row in enumerate(versions_raw):
        if not isinstance(row, dict):
            raise ValueError(f"{context}.versions[{i}] must be an object")
        allowed_keys = {"id", "path", "draft", "in_use", "name"}
        extra = set(row.keys()) - allowed_keys
        if extra:
            raise ValueError(f"{context}.versions[{i}] unexpected keys: {sorted(extra)}")
        for k in ("id", "path", "draft", "in_use"):
            if k not in row:
                raise ValueError(f"{context}.versions[{i}] missing {k!r}")
        vid = row["id"]
        path = row["path"]
        draft = row["draft"]
        in_use = row["in_use"]
        if not isinstance(vid, str) or not vid.strip():
            raise ValueError(f"{context}.versions[{i}].id invalid")
        if vid in seen_ids:
            raise ValueError(f"duplicate version id {vid!r} in {context}")
        seen_ids.add(vid)
        if not isinstance(path, str) or not _path_is_allowlisted(path):
            raise ValueError(f"invalid path for {context} / {vid!r}: {path!r}")
        if not isinstance(draft, bool) or not isinstance(in_use, bool):
            raise ValueError(f"draft/in_use must be booleans for {context} / {vid!r}")
        use = in_use
        if draft and in_use:
            use = False
        out_row: dict[str, Any] = {"id": vid, "path": path, "draft": draft, "in_use": use}
        if "name" in row and row["name"] is not None:
            nraw = row["name"]
            if not isinstance(nraw, str):
                raise ValueError(f"{context}.versions[{i}].name must be a string")
            nstrip = nraw.strip()
            if len(nstrip) > _MAX_VERSION_NAME_LEN:
                raise ValueError(
                    f"{context}.versions[{i}].name exceeds max length {_MAX_VERSION_NAME_LEN}",
                )
            if nstrip:
                out_row["name"] = nstrip
        versions_out.append(out_row)

    family_out: dict[str, Any] = {"versions": versions_out}
    slots_raw = fam_val.get("slots")
    if slots_raw is not None:
        if not isinstance(slots_raw, list):
            raise ValueError(f"{context}.slots must be an array")
        seen_slot_ids: set[str] = set()
        slots_out: list[str] = []
        for i, version_id in enumerate(slots_raw):
            if not isinstance(version_id, str):
                raise ValueError(f"{context}.slots[{i}] invalid")
            if version_id == "":
                slots_out.append("")
                continue
            if not version_id.strip():
                raise ValueError(f"{context}.slots[{i}] invalid")
            if version_id in seen_slot_ids:
                raise ValueError(f"duplicate slot version id {version_id!r} in {context}")
            if version_id not in seen_ids:
                raise ValueError(f"unknown slot version id {version_id!r} for {context}")
            seen_slot_ids.add(version_id)
            slots_out.append(version_id)
        family_out["slots"] = slots_out
    return family_out


def validate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate MRVC-1 / MRVC-2 / MRVC-3 / MRVC-8. Normalizes invalid draft+in_use for enemies
    and player. ``player`` holds versioned rows + slots; ``player_active_visual`` is derived
    from the first slot for backward compatibility.
    """
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")

    extra_top = set(data.keys()) - {"schema_version", "enemies", "player", "player_active_visual"}
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
        enemies_out[family] = _normalize_registry_family_block(f"enemies[{family!r}]", fam_val)

    pav_legacy = data.get("player_active_visual")
    player_raw = data.get("player")

    def _player_registry_nonempty(block: Any) -> bool:
        if not isinstance(block, dict):
            return False
        return bool(block.get("versions")) or bool(block.get("slots"))

    if isinstance(player_raw, dict) and _player_registry_nonempty(player_raw):
        player_block_in = player_raw
    elif pav_legacy is not None:
        if not isinstance(pav_legacy, dict):
            raise ValueError("player_active_visual must be null or an object")
        if set(pav_legacy.keys()) != {"path", "draft"}:
            raise ValueError("player_active_visual must have only path and draft")
        pp = pav_legacy["path"]
        pd = pav_legacy["draft"]
        if not isinstance(pp, str) or not _path_is_allowlisted(pp):
            raise ValueError(f"invalid player_active_visual.path: {pp!r}")
        if not isinstance(pd, bool):
            raise ValueError("player_active_visual.draft must be boolean")
        player_block_in = _legacy_pav_to_player_block(pav_legacy)
    elif isinstance(player_raw, dict):
        player_block_in = player_raw
    else:
        player_block_in = {"versions": [], "slots": []}

    player_normalized = _normalize_registry_family_block("player", player_block_in)
    pav_derived = _derive_player_active_visual_from_block(player_normalized)

    return {
        "schema_version": SCHEMA_VERSION,
        "enemies": enemies_out,
        "player": player_normalized,
        "player_active_visual": pav_derived,
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
    patches: dict[str, Any],
) -> dict[str, Any]:
    """Update one enemy version row; ``patches`` keys: draft, in_use, name (JSON ``null`` clears name)."""
    if not patches:
        raise ValueError("at least one patch field is required")
    allowed = frozenset({"draft", "in_use", "name"})
    bad = set(patches) - allowed
    if bad:
        raise ValueError(f"unsupported patch keys: {sorted(bad)}")

    data = load_effective_manifest(python_root)
    fam = data["enemies"].get(family)
    if fam is None:
        raise KeyError(f"unknown family: {family}")
    versions: list[dict[str, Any]] = fam["versions"]
    found = next((v for v in versions if v["id"] == version_id), None)
    if found is None:
        raise KeyError(f"unknown version {version_id!r} for family {family!r}")

    if "draft" in patches:
        d = patches["draft"]
        if not isinstance(d, bool):
            raise ValueError("patch draft must be boolean")
        found["draft"] = d
    if "in_use" in patches:
        u = patches["in_use"]
        if not isinstance(u, bool):
            raise ValueError("patch in_use must be boolean")
        found["in_use"] = u
    if "name" in patches:
        n = patches["name"]
        if n is None:
            found.pop("name", None)
        elif isinstance(n, str):
            s = n.strip()
            if not s:
                found.pop("name", None)
            elif len(s) > _MAX_VERSION_NAME_LEN:
                raise ValueError(f"name exceeds max length {_MAX_VERSION_NAME_LEN}")
            else:
                found["name"] = s
        else:
            raise ValueError("patch name must be string or null")

    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return validated


def patch_player_active_visual(
    python_root: Path,
    *,
    draft: bool | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Set the primary player model path (first slot). Creates version + slot rows as needed."""
    if draft is None and path is None:
        raise ValueError("at least one of draft or path must be set")

    data = load_effective_manifest(python_root)
    player_block = dict(data["player"])
    versions: list[dict[str, Any]] = list(player_block["versions"])
    slots: list[str] = list(player_block.get("slots") or [])

    if path is not None:
        if not _path_is_allowlisted(path):
            raise ValueError(f"invalid player path: {path!r}")
        if not path.endswith(".glb"):
            raise ValueError("player_active_visual.path must end with .glb")
        stem = Path(path).stem
        vid = stem if stem.strip() else "player_registry_00"
        row = next((v for v in versions if v["path"] == path), None)
        if row is None:
            row = next((v for v in versions if v["id"] == vid), None)
        if row is None:
            suffix = 0
            base_vid = vid
            while any(v["id"] == vid for v in versions):
                suffix += 1
                vid = f"{base_vid}_{suffix:02d}"
            row = {"id": vid, "path": path, "draft": False, "in_use": True}
            versions.append(row)
        else:
            vid = row["id"]
            row["draft"] = False
            row["in_use"] = True
        slots = [vid] + [s for s in slots if s != vid]
        player_block["versions"] = versions
        player_block["slots"] = slots

    if draft is not None:
        if draft:
            raise ValueError("player_active_visual cannot be draft")
        if slots:
            r0 = next((v for v in player_block["versions"] if v["id"] == slots[0]), None)
            if r0 is not None:
                r0["draft"] = False
                r0["in_use"] = True

    if path is None and not slots and draft is not None:
        raise ValueError("player_active_visual is unset; provide path to initialize")

    data["player"] = player_block
    data.pop("player_active_visual", None)
    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return validated


def get_enemy_slots(
    python_root: Path,
    family: str,
) -> dict[str, Any]:
    """Return currently configured slot IDs for a family."""
    data = load_effective_manifest(python_root)
    fam = data["enemies"].get(family)
    if fam is None:
        raise KeyError(f"unknown family: {family}")
    version_ids = list(fam.get("slots") or [])
    paths_by_id = {row["id"]: row["path"] for row in fam["versions"]}
    resolved_paths = [paths_by_id[version_id] for version_id in version_ids if version_id in paths_by_id]
    return {
        "family": family,
        "version_ids": version_ids,
        "resolved_paths": resolved_paths,
    }


def _discovered_animated_export_rows(
    python_root: Path,
    family: str,
    existing_ids: set[str],
    existing_paths: set[str],
) -> list[dict[str, Any]]:
    """
    Build new version dicts for ``animated_exports`` GLBs whose stem starts with
    ``{family}_animated_`` (procedural or prefab stems), exist on disk, and are not
    already represented by id or path in the manifest.
    """
    out: list[dict[str, Any]] = []
    prefix = f"{family}_animated_"
    export_dir = python_root / "animated_exports"
    if not export_dir.is_dir():
        return out
    for path in sorted(export_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".glb":
            continue
        stem = path.stem
        if not stem.startswith(prefix):
            continue
        rel = f"animated_exports/{path.name}"
        if not _path_is_allowlisted(rel):
            continue
        if stem in existing_ids or rel in existing_paths:
            continue
        out.append(
            {
                "id": stem,
                "path": rel,
                "draft": False,
                "in_use": False,
            },
        )
    return out


def sync_discovered_animated_glb_versions(python_root: Path, family: str) -> dict[str, Any]:
    """
    Persist new ``versions`` rows for on-disk animated GLBs under ``animated_exports/`` that
    match this family's export stem prefix but are absent from the manifest.

    New rows default to ``in_use: false`` so spawn pools are unchanged until the editor
    promotes them (e.g. via Add slot).
    """
    data = load_effective_manifest(python_root)
    fam = data["enemies"].get(family)
    if fam is None:
        raise KeyError(f"unknown family: {family}")
    versions = fam["versions"]
    existing_ids = {str(row["id"]) for row in versions if isinstance(row.get("id"), str)}
    existing_paths = {str(row["path"]) for row in versions if isinstance(row.get("path"), str)}
    new_rows = _discovered_animated_export_rows(python_root, family, existing_ids, existing_paths)
    if not new_rows:
        return data
    new_fam = {**fam, "versions": list(versions) + new_rows}
    new_data = {**data, "enemies": {**data["enemies"], family: new_fam}}
    validated = validate_manifest(new_data)
    save_manifest_atomic(python_root, validated)
    return validated


def patch_player_version(
    python_root: Path,
    version_id: str,
    patches: dict[str, Any],
) -> dict[str, Any]:
    """Update one player version row (same patch keys as ``patch_enemy_version``)."""
    if not patches:
        raise ValueError("at least one patch field is required")
    allowed = frozenset({"draft", "in_use", "name"})
    bad = set(patches) - allowed
    if bad:
        raise ValueError(f"unsupported patch keys: {sorted(bad)}")

    data = load_effective_manifest(python_root)
    fam = data["player"]
    versions: list[dict[str, Any]] = fam["versions"]
    found = next((v for v in versions if v["id"] == version_id), None)
    if found is None:
        raise KeyError(f"unknown player version {version_id!r}")

    if "draft" in patches:
        d = patches["draft"]
        if not isinstance(d, bool):
            raise ValueError("patch draft must be boolean")
        found["draft"] = d
    if "in_use" in patches:
        u = patches["in_use"]
        if not isinstance(u, bool):
            raise ValueError("patch in_use must be boolean")
        found["in_use"] = u
    if "name" in patches:
        n = patches["name"]
        if n is None:
            found.pop("name", None)
        elif isinstance(n, str):
            s = n.strip()
            if not s:
                found.pop("name", None)
            elif len(s) > _MAX_VERSION_NAME_LEN:
                raise ValueError(f"name exceeds max length {_MAX_VERSION_NAME_LEN}")
            else:
                found["name"] = s
        else:
            raise ValueError("patch name must be string or null")

    data.pop("player_active_visual", None)
    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return validated


def get_player_slots(python_root: Path) -> dict[str, Any]:
    data = load_effective_manifest(python_root)
    fam = data["player"]
    version_ids = list(fam.get("slots") or [])
    paths_by_id = {row["id"]: row["path"] for row in fam["versions"]}
    resolved_paths = [paths_by_id[version_id] for version_id in version_ids if version_id in paths_by_id]
    return {
        "family": "player",
        "version_ids": version_ids,
        "resolved_paths": resolved_paths,
    }


def _assert_assigned_slot_ids_unique(version_ids: list[str]) -> None:
    assigned = [x for x in version_ids if x != ""]
    if len(assigned) != len(set(assigned)):
        raise ValueError("duplicate version_ids are not allowed")


def put_player_slots(python_root: Path, version_ids: list[str]) -> dict[str, Any]:
    if not version_ids:
        raise ValueError("version_ids must not be empty")
    _assert_assigned_slot_ids_unique(version_ids)

    data = load_effective_manifest(python_root)
    fam = data["player"]
    versions = fam["versions"]
    versions_by_id = {row["id"]: row for row in versions}

    for version_id in version_ids:
        if version_id == "":
            continue
        row = versions_by_id.get(version_id)
        if row is None:
            raise KeyError(f"unknown player version {version_id!r}")
        if row.get("draft") is True:
            raise ValueError(f"player version {version_id!r} is draft and cannot be slotted")
        if row.get("in_use") is not True:
            raise ValueError(f"player version {version_id!r} is not in_use and cannot be slotted")

    fam["slots"] = list(version_ids)
    data.pop("player_active_visual", None)
    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return get_player_slots(python_root)


def _discovered_player_export_rows(
    python_root: Path,
    existing_ids: set[str],
    existing_paths: set[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    export_dir = python_root / "player_exports"
    if not export_dir.is_dir():
        return out
    for path in sorted(export_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".glb":
            continue
        stem = path.stem
        rel = f"player_exports/{path.name}"
        if not _path_is_allowlisted(rel):
            continue
        if stem in existing_ids or rel in existing_paths:
            continue
        out.append(
            {
                "id": stem,
                "path": rel,
                "draft": False,
                "in_use": False,
            },
        )
    return out


def sync_discovered_player_glb_versions(python_root: Path) -> dict[str, Any]:
    """Register ``player_exports/*.glb`` on disk that are missing from ``player.versions``."""
    data = load_effective_manifest(python_root)
    fam = data["player"]
    versions = fam["versions"]
    existing_ids = {str(row["id"]) for row in versions if isinstance(row.get("id"), str)}
    existing_paths = {str(row["path"]) for row in versions if isinstance(row.get("path"), str)}
    new_rows = _discovered_player_export_rows(python_root, existing_ids, existing_paths)
    if not new_rows:
        return data
    new_fam = {**fam, "versions": list(versions) + new_rows}
    new_data = {**data, "player": new_fam}
    new_data.pop("player_active_visual", None)
    validated = validate_manifest(new_data)
    save_manifest_atomic(python_root, validated)
    return validated


def put_enemy_slots(
    python_root: Path,
    family: str,
    version_ids: list[str],
) -> dict[str, Any]:
    """Replace slot IDs for a family, validating draft/in_use and duplicates."""
    if not version_ids:
        raise ValueError("version_ids must not be empty")
    _assert_assigned_slot_ids_unique(version_ids)

    data = load_effective_manifest(python_root)
    fam = data["enemies"].get(family)
    if fam is None:
        raise KeyError(f"unknown family: {family}")

    versions = fam["versions"]
    versions_by_id = {row["id"]: row for row in versions}

    for version_id in version_ids:
        if version_id == "":
            continue
        row = versions_by_id.get(version_id)
        if row is None:
            raise KeyError(f"unknown version {version_id!r} for family {family!r}")
        if row.get("draft") is True:
            raise ValueError(f"version {version_id!r} is draft and cannot be slotted")
        if row.get("in_use") is not True:
            raise ValueError(f"version {version_id!r} is not in_use and cannot be slotted")

    fam["slots"] = list(version_ids)
    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return get_enemy_slots(python_root, family)


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
