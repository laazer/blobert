"""HTTP API for ``model_registry.json`` (MRVC draft / in-use)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from core.config import settings
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/registry", tags=["registry"])

_ALLOWLIST_PREFIXES: tuple[str, ...] = (
    "animated_exports/",
    "exports/",
    "player_exports/",
    "level_exports/",
)
_MAX_URL_DECODE_PASSES = 3


def _load_registry_json_unvalidated(python_root: Path) -> dict[str, Any]:
    registry_file = python_root / "model_registry.json"
    if not registry_file.is_file():
        reg = _load_service()
        return reg.default_migrated_manifest()
    try:
        data = json.loads(registry_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError("invalid registry JSON") from e
    if not isinstance(data, dict):
        raise ValueError("registry payload must be an object")
    return data


def _normalize_registry_relative_glb_path(path: str) -> str:
    if any(ord(ch) < 32 for ch in path):
        raise ValueError("malformed target path class: control-character")
    if "\\" in path:
        raise ValueError("malformed target path class: mixed-separator")
    if path.startswith("res://"):
        raise HTTPException(status_code=403, detail="forbidden target path class: res-path")
    if path.startswith("/"):
        raise HTTPException(status_code=403, detail="forbidden target path class: absolute-path")

    decoded = path
    for _ in range(_MAX_URL_DECODE_PASSES):
        next_decoded = unquote(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded

    if any(ord(ch) < 32 for ch in decoded):
        raise ValueError("malformed target path class: control-character")
    if "%" in decoded:
        raise ValueError("malformed target path class: malformed-encoding")

    parts = decoded.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("malformed target path class: traversal")
    if not decoded.endswith(".glb"):
        raise ValueError("malformed target path class: extension")
    if not any(decoded.startswith(prefix) for prefix in _ALLOWLIST_PREFIXES):
        raise HTTPException(status_code=403, detail="forbidden target path class: allowlist-prefix")
    return decoded


def _safe_is_file_under_python_root(python_root: Path, rel_path: str) -> bool:
    try:
        return (python_root / rel_path).is_file()
    except OSError:
        return False


def _player_export_rows_for_load_existing(data: dict[str, Any]) -> list[dict[str, str]]:
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
                    canonical = _normalize_registry_relative_glb_path(path)
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
                canonical = _normalize_registry_relative_glb_path(ppath)
            except (HTTPException, ValueError):
                return out
            name = Path(ppath).name
            stem = name[:-4] if name.lower().endswith(".glb") else Path(ppath).stem
            vid = stem.strip() or "player_registry_00"
            out.append({"kind": "player", "version_id": vid, "path": canonical})
    return out


def _load_existing_candidates_from_registry(python_root: Path) -> list[dict[str, str]]:
    data = _load_registry_json_unvalidated(python_root)
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
                    canonical = _normalize_registry_relative_glb_path(path)
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
    player_rows = _player_export_rows_for_load_existing(data)
    player_rows.sort(key=lambda row: row["version_id"])
    return rows + player_rows


def _resolve_enemy_identity_path(
    python_root: Path,
    family: str,
    version_id: str,
) -> str:
    for row in _load_existing_candidates_from_registry(python_root):
        if row.get("kind") != "enemy":
            continue
        if row.get("family") == family and row.get("version_id") == version_id:
            return row["path"]
    raise KeyError(f"unknown version {version_id!r} for family {family!r}")


def _resolve_player_identity_path(python_root: Path, version_id: str) -> str:
    for row in _load_existing_candidates_from_registry(python_root):
        if row.get("kind") != "player":
            continue
        if row.get("version_id") == version_id:
            return row["path"]
    raise KeyError(f"unknown player version id {version_id!r}")


def _canonical_python_roots() -> tuple[Path, Path]:
    """``asset_generation/python`` and its ``src/`` (same layout as ``core.config`` defaults)."""
    backend_dir = Path(__file__).resolve().parent.parent
    asset_generation = backend_dir.parent.parent
    root = asset_generation / "python"
    return root, root / "src"


def _ensure_python_import_path() -> None:
    """
    Legacy hook: import paths are set in ``main.py`` before routers load.

    ``settings.python_root`` may point at an isolated tmp dir in tests; manifest
    I/O uses that path, but ``utils`` / ``model_registry`` resolve from the
    canonical checkout via ``main._bootstrap_asset_generation_python_path``.
    """
    return


def _load_service():
    # Deferred imports are required because router module import happens before runtime path
    # injection; importing these modules at file import time can fail in test/app startup.
    from src.utils.blender_stubs import ensure_blender_stubs

    ensure_blender_stubs()
    from src.model_registry import service as reg

    return reg


class EnemyVersionPatch(BaseModel):
    draft: bool | None = Field(default=None, description="Draft flag; draft entries are not spawn-eligible.")
    in_use: bool | None = Field(default=None, description="In-use (spawn pool) flag; ignored if draft.")
    name: str | None = Field(
        default=None,
        description="Optional display name; omit for no change, null or empty string clears.",
    )


class PlayerVisualPatch(BaseModel):
    draft: bool | None = None
    path: str | None = Field(default=None, description="Allowlisted path under python_root.")


class EnemySlotsPut(BaseModel):
    version_ids: list[str] = Field(default_factory=list, description="Ordered slot IDs for a family.")


class EnemyVersionDeleteRequest(BaseModel):
    delete_files: bool = False
    confirm: bool = False
    confirm_text: str | None = None
    target_path: str | None = None


class PlayerActiveVisualDeleteRequest(BaseModel):
    confirm: bool = False


class LoadExistingOpenRequest(BaseModel):
    kind: str = Field(description="One of enemy|player|path for constrained load-open.")
    family: str | None = None
    version_id: str | None = None
    path: str | None = None


@router.get("/model/load_existing/candidates")
async def get_load_existing_candidates() -> JSONResponse:
    try:
        candidates = _load_existing_candidates_from_registry(settings.python_root)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse({"candidates": candidates})


@router.post("/model/load_existing/open")
async def open_load_existing(body: LoadExistingOpenRequest) -> JSONResponse:
    if body.path is not None and (body.family is not None or body.version_id is not None):
        raise HTTPException(status_code=400, detail="malformed target payload: mixed-identity-and-path")
    try:
        if body.kind == "enemy":
            if body.family is None or body.version_id is None or body.path is not None:
                raise HTTPException(status_code=400, detail="malformed target payload: enemy-requires-identity")
            canonical_path = _resolve_enemy_identity_path(settings.python_root, body.family, body.version_id)
            if not _safe_is_file_under_python_root(settings.python_root, canonical_path):
                raise HTTPException(status_code=404, detail="registry target file not found")
            return JSONResponse(
                {
                    "kind": "enemy",
                    "family": body.family,
                    "version_id": body.version_id,
                    "path": canonical_path,
                },
            )
        if body.kind == "player":
            if body.family is not None or body.path is not None or body.version_id is None:
                raise HTTPException(status_code=400, detail="malformed target payload: player-requires-version-id")
            canonical_path = _resolve_player_identity_path(settings.python_root, body.version_id)
            if not _safe_is_file_under_python_root(settings.python_root, canonical_path):
                raise HTTPException(status_code=404, detail="registry target file not found")
            return JSONResponse(
                {
                    "kind": "player",
                    "version_id": body.version_id,
                    "path": canonical_path,
                },
            )
        if body.kind == "path":
            if body.path is None or body.family is not None or body.version_id is not None:
                raise HTTPException(status_code=400, detail="malformed target payload: path-requires-path-only")
            canonical_path = _normalize_registry_relative_glb_path(body.path)
            if not _safe_is_file_under_python_root(settings.python_root, canonical_path):
                raise HTTPException(status_code=404, detail="registry target file not found")
            return JSONResponse({"kind": "path", "path": canonical_path})
        raise HTTPException(status_code=400, detail="malformed target payload: unsupported-kind")
    except HTTPException:
        raise
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e


@router.get("/model")
async def get_model_registry() -> JSONResponse:
    try:
        reg = _load_service()
        data = reg.load_effective_manifest(settings.python_root)
    except ValueError as e:
        logger.warning("registry get: validation error — %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ImportError as e:
        logger.warning("registry get: ImportError — %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(data)


@router.patch("/model/enemies/{family}/versions/{version_id}")
async def patch_enemy_version_endpoint(
    family: str,
    version_id: str,
    body: EnemyVersionPatch,
) -> JSONResponse:
    patches = body.model_dump(exclude_unset=True)
    if not patches:
        raise HTTPException(status_code=400, detail="provide at least one field to patch")

    try:
        reg = _load_service()
        updated = reg.patch_enemy_version(settings.python_root, family, version_id, patches)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(updated)


@router.patch("/model/player_active_visual")
async def patch_player_active_visual_endpoint(body: PlayerVisualPatch) -> JSONResponse:
    if body.draft is None and body.path is None:
        raise HTTPException(status_code=400, detail="provide draft and/or path")

    try:
        reg = _load_service()
        updated = reg.patch_player_active_visual(
            settings.python_root,
            draft=body.draft,
            path=body.path,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(updated)


@router.get("/model/enemies/{family}/slots")
async def get_enemy_slots_endpoint(family: str) -> JSONResponse:
    try:
        reg = _load_service()
        payload = reg.get_enemy_slots(settings.python_root, family)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(payload)


@router.post("/model/enemies/{family}/sync_animated_exports")
async def post_sync_animated_exports_endpoint(family: str) -> JSONResponse:
    """Register on-disk ``animated_exports/{family}_animated_*.glb`` files missing from the manifest."""
    try:
        reg = _load_service()
        updated = reg.sync_discovered_animated_glb_versions(settings.python_root, family)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(updated)


@router.put("/model/enemies/{family}/slots")
async def put_enemy_slots_endpoint(
    family: str,
    body: EnemySlotsPut,
) -> JSONResponse:
    try:
        reg = _load_service()
        payload = reg.put_enemy_slots(settings.python_root, family, body.version_ids)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(payload)


@router.get("/model/player/slots")
async def get_player_slots_endpoint() -> JSONResponse:
    try:
        reg = _load_service()
        payload = reg.get_player_slots(settings.python_root)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(payload)


@router.put("/model/player/slots")
async def put_player_slots_endpoint(body: EnemySlotsPut) -> JSONResponse:
    try:
        reg = _load_service()
        payload = reg.put_player_slots(settings.python_root, body.version_ids)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(payload)


@router.post("/model/player/sync_player_exports")
async def post_sync_player_exports_endpoint() -> JSONResponse:
    """Register on-disk ``player_exports/*.glb`` files missing from the manifest."""
    try:
        reg = _load_service()
        updated = reg.sync_discovered_player_glb_versions(settings.python_root)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    return JSONResponse(updated)


@router.get("/model/spawn_eligible/{family}")
async def get_spawn_eligible(family: str) -> JSONResponse:
    """Consumer-facing view: paths eligible for default spawn pool (MRVC-4)."""
    try:
        reg = _load_service()
        manifest = reg.load_effective_manifest(settings.python_root)
        paths = reg.spawn_eligible_paths(manifest, family)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
    payload: dict[str, Any] = {"family": family, "paths": paths}
    return JSONResponse(payload)


def _require_delete_confirmation(confirm: bool) -> None:
    if not confirm:
        raise HTTPException(status_code=400, detail="delete requires explicit confirmation")


def _find_enemy_version(manifest: dict[str, Any], family: str, version_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    enemies = manifest.get("enemies")
    if not isinstance(enemies, dict):
        raise HTTPException(status_code=400, detail="malformed target payload: missing-enemies")
    fam = enemies.get(family)
    if not isinstance(fam, dict):
        raise HTTPException(status_code=404, detail="unknown target")
    versions = fam.get("versions")
    if not isinstance(versions, list):
        raise HTTPException(status_code=400, detail="malformed target payload: missing-versions")
    for row in versions:
        if isinstance(row, dict) and row.get("id") == version_id:
            return fam, row
    raise HTTPException(status_code=404, detail="unknown target")


def _normalized_target_path_or_row_path(
    row_path: str,
    request_target_path: str | None,
) -> str:
    if request_target_path is None:
        return _normalize_registry_relative_glb_path(row_path)
    normalized = _normalize_registry_relative_glb_path(request_target_path)
    if normalized != row_path:
        raise HTTPException(status_code=403, detail="forbidden target path class: target-mismatch")
    return normalized


def _apply_enemy_version_delete(
    manifest: dict[str, Any],
    family: str,
    version_id: str,
) -> None:
    fam, row = _find_enemy_version(manifest, family, version_id)
    versions = fam["versions"]
    versions[:] = [version for version in versions if version is not row]
    slots = fam.get("slots")
    if isinstance(slots, list):
        fam["slots"] = [slot for slot in slots if slot != version_id]


@router.delete("/model/enemies/{family}/versions/{version_id}")
async def delete_enemy_version_endpoint(
    family: str,
    version_id: str,
    body: EnemyVersionDeleteRequest,
) -> JSONResponse:
    _require_delete_confirmation(body.confirm)
    try:
        reg = _load_service()
        manifest = reg.load_effective_manifest(settings.python_root)
        fam, row = _find_enemy_version(manifest, family, version_id)

        row_path_raw = row.get("path")
        if not isinstance(row_path_raw, str):
            raise HTTPException(status_code=400, detail="malformed target payload: missing-path")
        row_path = _normalized_target_path_or_row_path(row_path_raw, body.target_path)
        is_draft = row.get("draft") is True
        is_in_use = row.get("in_use") is True and not is_draft

        if is_draft:
            if body.confirm_text is not None:
                expected = f"delete draft {family} {version_id}"
                if body.confirm_text.strip() != expected:
                    raise HTTPException(status_code=400, detail="malformed confirmation text")
        elif is_in_use:
            expected = f"delete in-use {family} {version_id}"
            if (body.confirm_text or "").strip() != expected:
                raise HTTPException(status_code=400, detail="malformed confirmation text")
            live_rows = [
                candidate
                for candidate in fam.get("versions", [])
                if isinstance(candidate, dict)
                and candidate.get("id") != version_id
                and candidate.get("draft") is False
                and candidate.get("in_use") is True
            ]
            if not live_rows:
                raise HTTPException(status_code=409, detail="cannot delete sole in-use enemy version")
        else:
            raise HTTPException(status_code=400, detail="delete requires draft or in-use target")

        _apply_enemy_version_delete(manifest, family, version_id)
        validated = reg.validate_manifest(manifest)
        reg.save_manifest_atomic(settings.python_root, validated)
        if body.delete_files:
            target_file = settings.python_root / row_path
            if target_file.exists():
                target_file.unlink()
        return JSONResponse(validated)
    except HTTPException:
        raise
    except KeyError as e:
        raise HTTPException(status_code=404, detail="unknown target") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e


@router.delete("/model/player_active_visual")
async def delete_player_active_visual_endpoint(body: PlayerActiveVisualDeleteRequest) -> JSONResponse:
    _require_delete_confirmation(body.confirm)
    try:
        reg = _load_service()
        manifest = reg.load_effective_manifest(settings.python_root)
        if manifest.get("player_active_visual") is None:
            raise HTTPException(status_code=404, detail="unknown target")
        player = manifest["player"]
        assigned_slots = [s for s in (player.get("slots") or []) if s]
        if len(assigned_slots) <= 1:
            raise HTTPException(status_code=409, detail="cannot delete sole active player visual")
        # Unslot the current active (first assigned slot entry)
        old_slots = list(player.get("slots") or [])
        first_assigned = next((s for s in old_slots if s), None)
        player["slots"] = ["" if s == first_assigned else s for s in old_slots]
        manifest.pop("player_active_visual", None)
        validated = reg.validate_manifest(manifest)
        reg.save_manifest_atomic(settings.python_root, validated)
        return JSONResponse(validated)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
