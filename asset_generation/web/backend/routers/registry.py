"""HTTP API for ``model_registry.json`` (MRVC draft / in-use)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from core.config import settings
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from services.python_bridge import bootstrap_python_runtime
from services.registry_mutation import load_model_registry_service
from services.registry_query import (
    load_existing_candidates_from_registry,
    normalize_registry_relative_glb_path_for_http,
    resolve_enemy_identity_path,
    resolve_player_identity_path,
    safe_is_file_under_python_root,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/registry", tags=["registry"])


def _canonical_python_roots() -> tuple[Path, Path]:
    """Legacy seam for CI import-standardization contract checks."""
    backend_root = Path(__file__).resolve().parents[1]
    python_root = backend_root.parents[1] / "python"
    return python_root, python_root / "src"


def _ensure_python_import_path() -> Path:
    """Legacy entrypoint now delegated to shared python bridge bootstrap."""
    return bootstrap_python_runtime()


def _load_service():
    return load_model_registry_service()


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
        candidates = load_existing_candidates_from_registry(settings.python_root)
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
            canonical_path = resolve_enemy_identity_path(settings.python_root, body.family, body.version_id)
            if not safe_is_file_under_python_root(settings.python_root, canonical_path):
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
            canonical_path = resolve_player_identity_path(settings.python_root, body.version_id)
            if not safe_is_file_under_python_root(settings.python_root, canonical_path):
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
            canonical_path = normalize_registry_relative_glb_path_for_http(body.path)
            if not safe_is_file_under_python_root(settings.python_root, canonical_path):
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


@router.delete("/model/enemies/{family}/versions/{version_id}")
async def delete_enemy_version_endpoint(
    family: str,
    version_id: str,
    body: EnemyVersionDeleteRequest,
) -> JSONResponse:
    try:
        reg = _load_service()
        updated = reg.delete_enemy_version(
            settings.python_root,
            family=family,
            version_id=version_id,
            confirm=body.confirm,
            confirm_text=body.confirm_text,
            target_path=body.target_path,
            delete_files=body.delete_files,
        )
        return JSONResponse(updated)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="unknown target") from e
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        detail = str(e)
        if detail.startswith("forbidden target path class:"):
            raise HTTPException(status_code=403, detail=detail) from e
        raise HTTPException(status_code=400, detail=detail) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e


@router.delete("/model/player_active_visual")
async def delete_player_active_visual_endpoint(body: PlayerActiveVisualDeleteRequest) -> JSONResponse:
    try:
        reg = _load_service()
        updated = reg.delete_player_active_visual(
            settings.python_root,
            confirm=body.confirm,
        )
        return JSONResponse(updated)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="unknown target") from e
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"registry unavailable: {e}") from e
