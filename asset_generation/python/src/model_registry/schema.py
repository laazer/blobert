"""Manifest schema normalization and validation for `model_registry.json`."""

from __future__ import annotations

from typing import Any, TypedDict

from .migrations import (
    SCHEMA_VERSION,
    _derive_player_active_visual_from_block,
    _legacy_pav_to_player_block,
)

ALLOWLIST_PREFIXES: tuple[str, ...] = (
    "animated_exports/",
    "exports/",
    "player_exports/",
    "level_exports/",
)
REGISTRY_FILENAME = "model_registry.json"
_MAX_VERSION_NAME_LEN = 128


class VersionRow(TypedDict, total=False):
    id: str
    path: str
    draft: bool
    in_use: bool
    name: str


class FamilyBlock(TypedDict, total=False):
    versions: list[VersionRow]
    slots: list[str]


class Manifest(TypedDict):
    schema_version: int
    enemies: dict[str, FamilyBlock]
    player: FamilyBlock
    player_active_visual: dict[str, Any] | None


def _path_is_allowlisted(path: str) -> bool:
    if not path or path.startswith("/") or ".." in path.split("/"):
        return False
    return any(path.startswith(p) for p in ALLOWLIST_PREFIXES)


def _coerce_version_row_draft_in_use(row: dict[str, Any]) -> None:
    d = bool(row["draft"])
    u = bool(row["in_use"])
    if d and u:
        row["in_use"] = False
    elif not d and not u:
        row["draft"] = True
        row["in_use"] = False


def _normalize_registry_family_block(context: str, fam_val: Any) -> dict[str, Any]:
    """Validate and canonicalize one family block (`versions` + optional `slots`)."""
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
        if not draft and not use:
            draft = True
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
            slot_row = next((r for r in versions_out if r["id"] == version_id), None)
            if slot_row is not None and (slot_row.get("draft") or not slot_row.get("in_use")):
                slots_out.append("")
                continue
            seen_slot_ids.add(version_id)
            slots_out.append(version_id)
        family_out["slots"] = slots_out
    return family_out


def validate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """Validate top-level manifest fields and return canonicalized schema output."""
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
