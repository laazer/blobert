"""
Load / validate / persist ``model_registry.json`` (MRVC).

Consumer: ``spawn_eligible_paths`` implements MRVC-4 default pool filtering
(non-draft and in-use only).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from .migrations import (
    default_migrated_manifest,
)
from .schema import _MAX_VERSION_NAME_LEN, _path_is_allowlisted, validate_manifest
from .store import read_registry_object, write_registry_json_atomic

_MAX_URL_DECODE_PASSES = 3
_WINDOWS_DRIVE_PATH_RE = re.compile(r"^[a-zA-Z]:[/\\]")


def normalize_registry_relative_glb_path(
    raw_path: str,
    *,
    allow_uppercase_extension: bool = False,
) -> str:
    """Canonicalize and validate untrusted registry-relative GLB paths."""
    if any(ord(ch) < 32 for ch in raw_path):
        raise ValueError("malformed target path class: control-character")
    if "\\" in raw_path:
        raise ValueError("malformed target path class: mixed-separator")

    decoded = raw_path
    for _ in range(_MAX_URL_DECODE_PASSES):
        next_decoded = unquote(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded

    if any(ord(ch) < 32 for ch in decoded):
        raise ValueError("malformed target path class: control-character")
    if "%" in decoded:
        raise ValueError("malformed target path class: malformed-encoding")

    cleaned = decoded.strip()
    if not cleaned:
        raise ValueError("malformed target path class: empty")
    if cleaned.startswith("res://"):
        raise ValueError("forbidden target path class: res-path")
    if cleaned.startswith("/"):
        raise ValueError("forbidden target path class: absolute-path")
    if cleaned.startswith("//"):
        raise ValueError("forbidden target path class: absolute-path")
    if _WINDOWS_DRIVE_PATH_RE.match(cleaned):
        raise ValueError("forbidden target path class: absolute-path")

    canonical_parts: list[str] = []
    for part in cleaned.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError("malformed target path class: traversal")
        canonical_parts.append(part)

    if not canonical_parts:
        raise ValueError("malformed target path class: empty")

    canonical = "/".join(canonical_parts)
    if canonical.endswith(".glb"):
        pass
    elif allow_uppercase_extension and canonical.lower().endswith(".glb"):
        canonical = f"{canonical[:-3]}glb"
    else:
        raise ValueError("malformed target path class: extension")
    if not _path_is_allowlisted(canonical):
        raise ValueError("forbidden target path class: allowlist-prefix")
    return canonical


def _coerce_version_row_draft_in_use(row: dict[str, Any]) -> None:
    d = bool(row["draft"])
    u = bool(row["in_use"])
    if d and u:
        row["in_use"] = False
    elif not d and not u:
        row["draft"] = True
        row["in_use"] = False


def _get_family_block(data: dict[str, Any], family: str) -> dict[str, Any]:
    if family == "player":
        return data["player"]
    fam = data["enemies"].get(family)
    if fam is None:
        raise KeyError(f"unknown family: {family!r}")
    return fam


def _evict_from_slots(fam_block: dict[str, Any], version_id: str) -> None:
    slots = fam_block.get("slots")
    if isinstance(slots, list):
        fam_block["slots"] = ["" if s == version_id else s for s in slots]


def _apply_version_patches(
    fam_block: dict[str, Any],
    version_id: str,
    patches: dict[str, Any],
) -> None:
    versions: list[dict[str, Any]] = fam_block["versions"]
    found = next((v for v in versions if v["id"] == version_id), None)
    if found is None:
        raise KeyError(f"unknown version {version_id!r}")

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

    _coerce_version_row_draft_in_use(found)
    if found.get("draft"):
        _evict_from_slots(fam_block, version_id)


def load_effective_manifest(python_root: Path) -> dict[str, Any]:
    raw = read_registry_object(python_root)
    if raw is None:
        return default_migrated_manifest()
    return validate_manifest(raw)


def save_manifest_atomic(python_root: Path, data: dict[str, Any]) -> None:
    validated = validate_manifest(data)
    write_registry_json_atomic(python_root, validated, replace_fn=os.replace)


def patch_enemy_version(
    python_root: Path,
    family: str,
    version_id: str,
    patches: dict[str, Any],
) -> dict[str, Any]:
    if not patches:
        raise ValueError("at least one patch field is required")
    bad = set(patches) - frozenset({"draft", "in_use", "name"})
    if bad:
        raise ValueError(f"unsupported patch keys: {sorted(bad)}")

    data = load_effective_manifest(python_root)
    fam = _get_family_block(data, family)
    _apply_version_patches(fam, version_id, patches)
    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return validated


def _require_delete_confirmation(confirm: bool) -> None:
    if not confirm:
        raise ValueError("delete requires explicit confirmation")


def _find_enemy_version(
    manifest: dict[str, Any],
    family: str,
    version_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    enemies = manifest.get("enemies")
    if not isinstance(enemies, dict):
        raise ValueError("malformed target payload: missing-enemies")
    fam = enemies.get(family)
    if not isinstance(fam, dict):
        raise KeyError("unknown target")
    versions = fam.get("versions")
    if not isinstance(versions, list):
        raise ValueError("malformed target payload: missing-versions")
    for row in versions:
        if isinstance(row, dict) and row.get("id") == version_id:
            return fam, row
    raise KeyError("unknown target")


def _normalized_target_path_or_row_path(
    row_path: str,
    request_target_path: str | None,
) -> str:
    normalized_row_path = normalize_registry_relative_glb_path(row_path)
    if request_target_path is None:
        return normalized_row_path
    normalized_target = normalize_registry_relative_glb_path(request_target_path)
    if normalized_target != normalized_row_path:
        raise ValueError("forbidden target path class: target-mismatch")
    return normalized_target


def _apply_enemy_version_delete(
    manifest: dict[str, Any],
    family: str,
    version_id: str,
) -> None:
    fam, row = _find_enemy_version(manifest, family, version_id)
    versions = fam["versions"]
    versions[:] = [version for version in versions if version is not row]
    _evict_from_slots(fam, version_id)


def delete_enemy_version(
    python_root: Path,
    *,
    family: str,
    version_id: str,
    confirm: bool,
    confirm_text: str | None = None,
    target_path: str | None = None,
    delete_files: bool = False,
) -> dict[str, Any]:
    _require_delete_confirmation(confirm)

    manifest = load_effective_manifest(python_root)
    fam, row = _find_enemy_version(manifest, family, version_id)
    row_path_raw = row.get("path")
    if not isinstance(row_path_raw, str):
        raise ValueError("malformed target payload: missing-path")
    row_path = _normalized_target_path_or_row_path(row_path_raw, target_path)
    is_draft = row.get("draft") is True
    is_in_use = row.get("in_use") is True and not is_draft

    if is_draft:
        if confirm_text is not None:
            expected = f"delete draft {family} {version_id}"
            if confirm_text.strip() != expected:
                raise ValueError("malformed confirmation text")
    elif is_in_use:
        expected = f"delete in-use {family} {version_id}"
        if (confirm_text or "").strip() != expected:
            raise ValueError("malformed confirmation text")
        live_rows = [
            candidate
            for candidate in fam.get("versions", [])
            if isinstance(candidate, dict)
            and candidate.get("id") != version_id
            and candidate.get("draft") is False
            and candidate.get("in_use") is True
        ]
        if not live_rows:
            raise RuntimeError("cannot delete sole in-use enemy version")
    else:
        raise ValueError("delete requires draft or in-use target")

    _apply_enemy_version_delete(manifest, family, version_id)
    validated = validate_manifest(manifest)
    save_manifest_atomic(python_root, validated)
    if delete_files:
        target_file = python_root / row_path
        if target_file.exists():
            target_file.unlink()
    return validated


def delete_player_active_visual(
    python_root: Path,
    *,
    confirm: bool,
) -> dict[str, Any]:
    _require_delete_confirmation(confirm)
    manifest = load_effective_manifest(python_root)
    if manifest.get("player_active_visual") is None:
        raise KeyError("unknown target")
    player = manifest["player"]
    assigned_slots = [slot_id for slot_id in (player.get("slots") or []) if slot_id]
    if len(assigned_slots) <= 1:
        raise RuntimeError("cannot delete sole active player visual")
    old_slots = list(player.get("slots") or [])
    first_assigned = next((slot_id for slot_id in old_slots if slot_id), None)
    player["slots"] = ["" if slot_id == first_assigned else slot_id for slot_id in old_slots]
    manifest.pop("player_active_visual", None)
    validated = validate_manifest(manifest)
    validated.pop("player_active_visual", None)
    write_registry_json_atomic(python_root, validated, replace_fn=os.replace)
    return validated


def patch_player_active_visual(
    python_root: Path,
    *,
    draft: bool | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Set or initialize the active player visual via player versions/slots."""
    if draft is None and path is None:
        raise ValueError("at least one of draft or path must be set")

    data = load_effective_manifest(python_root)
    player_block = dict(data["player"])
    versions: list[dict[str, Any]] = list(player_block["versions"])
    slots: list[str] = list(player_block.get("slots") or [])

    if path is not None:
        if path != path.strip():
            raise ValueError("player path must end with .glb")
        try:
            path = normalize_registry_relative_glb_path(path)
        except ValueError as exc:
            if "extension" in str(exc):
                raise ValueError("player path must end with .glb") from exc
            raise ValueError("invalid player path") from exc
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


def _slots_payload(fam_block: dict[str, Any], family: str) -> dict[str, Any]:
    version_ids = list(fam_block.get("slots") or [])
    paths_by_id = {row["id"]: row["path"] for row in fam_block["versions"]}
    resolved_paths = [paths_by_id[vid] for vid in version_ids if vid and vid in paths_by_id]
    return {"family": family, "version_ids": version_ids, "resolved_paths": resolved_paths}


def get_enemy_slots(python_root: Path, family: str) -> dict[str, Any]:
    data = load_effective_manifest(python_root)
    fam = _get_family_block(data, family)
    return _slots_payload(fam, family)


def _discovered_animated_export_rows(
    python_root: Path,
    family: str,
    existing_ids: set[str],
    existing_paths: set[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    prefix = f"{family}_animated_"
    scan_dirs: tuple[tuple[Path, str], ...] = (
        (python_root / "animated_exports", "animated_exports"),
        (python_root / "animated_exports" / "draft", "animated_exports/draft"),
    )
    for export_dir, rel_prefix in scan_dirs:
        if not export_dir.is_dir():
            continue
        for path in sorted(export_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() != ".glb":
                continue
            stem = path.stem
            if not stem.startswith(prefix):
                continue
            rel = f"{rel_prefix}/{path.name}"
            try:
                canonical_rel = normalize_registry_relative_glb_path(
                    rel,
                    allow_uppercase_extension=True,
                )
            except ValueError:
                continue
            if stem in existing_ids or canonical_rel in existing_paths:
                continue
            out.append(
                {
                    "id": stem,
                    "path": canonical_rel,
                    "draft": True,
                    "in_use": False,
                },
            )
    return out


def sync_discovered_animated_glb_versions(python_root: Path, family: str) -> dict[str, Any]:
    """Append newly discovered family animated GLB exports as draft rows."""
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
    if not patches:
        raise ValueError("at least one patch field is required")
    bad = set(patches) - frozenset({"draft", "in_use", "name"})
    if bad:
        raise ValueError(f"unsupported patch keys: {sorted(bad)}")

    data = load_effective_manifest(python_root)
    fam = _get_family_block(data, "player")
    _apply_version_patches(fam, version_id, patches)
    data.pop("player_active_visual", None)
    validated = validate_manifest(data)
    save_manifest_atomic(python_root, validated)
    return validated


def get_player_slots(python_root: Path) -> dict[str, Any]:
    data = load_effective_manifest(python_root)
    return _slots_payload(data["player"], "player")


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
    versions_by_id = {row["id"]: row for row in fam["versions"]}

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
    return _slots_payload(validated["player"], "player")


def _discovered_player_export_rows(
    python_root: Path,
    existing_ids: set[str],
    existing_paths: set[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    scan_dirs: tuple[tuple[Path, str], ...] = (
        (python_root / "player_exports", "player_exports"),
        (python_root / "player_exports" / "draft", "player_exports/draft"),
    )
    for export_dir, rel_prefix in scan_dirs:
        if not export_dir.is_dir():
            continue
        for path in sorted(export_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() != ".glb":
                continue
            stem = path.stem
            rel = f"{rel_prefix}/{path.name}"
            try:
                canonical_rel = normalize_registry_relative_glb_path(
                    rel,
                    allow_uppercase_extension=True,
                )
            except ValueError:
                continue
            if stem in existing_ids or canonical_rel in existing_paths:
                continue
            out.append(
                {
                    "id": stem,
                    "path": canonical_rel,
                    "draft": True,
                    "in_use": False,
                },
            )
    return out


def sync_discovered_player_glb_versions(python_root: Path) -> dict[str, Any]:
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
    if not version_ids:
        raise ValueError("version_ids must not be empty")
    _assert_assigned_slot_ids_unique(version_ids)

    data = load_effective_manifest(python_root)
    fam = _get_family_block(data, family)
    versions_by_id = {row["id"]: row for row in fam["versions"]}

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
    return _slots_payload(_get_family_block(validated, family), family)


def spawn_eligible_paths(manifest: dict[str, Any], family: str) -> list[str]:
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
