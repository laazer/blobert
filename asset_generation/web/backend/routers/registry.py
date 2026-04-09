"""HTTP API for ``model_registry.json`` (MRVC draft / in-use)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from core.config import settings
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/registry", tags=["registry"])


def _canonical_python_roots() -> tuple[Path, Path]:
    """``asset_generation/python`` and its ``src/`` (same layout as ``core.config`` defaults)."""
    backend_dir = Path(__file__).resolve().parent.parent
    asset_generation = backend_dir.parent.parent
    root = asset_generation / "python"
    return root, root / "src"


def _ensure_python_import_path() -> None:
    """
    Import pipeline code from the repo's ``asset_generation/python`` tree.

    ``settings.python_root`` may point at an isolated tmp dir in tests; manifest
    I/O uses that path, but ``utils`` / ``model_registry`` must resolve from the
    canonical checkout.
    """
    py_root, src_path = _canonical_python_roots()
    for p in (str(py_root), str(src_path)):
        if p not in sys.path:
            sys.path.insert(0, p)


def _load_service():
    _ensure_python_import_path()
    from utils.blender_stubs import ensure_blender_stubs

    ensure_blender_stubs()
    from model_registry import service as reg

    return reg


class EnemyVersionPatch(BaseModel):
    draft: bool | None = Field(default=None, description="Draft flag; draft entries are not spawn-eligible.")
    in_use: bool | None = Field(default=None, description="In-use (spawn pool) flag; ignored if draft.")


class PlayerVisualPatch(BaseModel):
    draft: bool | None = None
    path: str | None = Field(default=None, description="Allowlisted path under python_root.")


class EnemySlotsPut(BaseModel):
    version_ids: list[str] = Field(default_factory=list, description="Ordered slot IDs for a family.")


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
    if body.draft is None and body.in_use is None:
        raise HTTPException(status_code=400, detail="provide draft and/or in_use")

    try:
        reg = _load_service()
        updated = reg.patch_enemy_version(
            settings.python_root,
            family,
            version_id,
            draft=body.draft,
            in_use=body.in_use,
        )
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
