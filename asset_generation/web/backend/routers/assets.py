import logging
from pathlib import Path

from core.config import settings
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from services.error_mapping import map_exception_to_http
from services.python_bridge import import_asset_module

router = APIRouter(prefix="/api/assets", tags=["assets"])
logger = logging.getLogger(__name__)

_EXPORT_DIRS = [
    "animated_exports",
    "exports",
    "player_exports",
    "level_exports",
]

_MIME = {
    ".glb": "model/gltf-binary",
    ".json": "application/json",
}


class ListedAsset(BaseModel):
    """One file entry from an export directory (ARGLB-1)."""

    model_config = ConfigDict(extra="forbid")

    path: str
    name: str
    dir: str
    size: int


class TextureAssetMetadata(BaseModel):
    """Metadata for a pre-supplied texture asset."""

    model_config = ConfigDict(extra="forbid")

    id: str
    filename: str
    display_name: str
    description: str
    layout: str
    width: int
    height: int
    tiling_supported: bool


def _append_glb_json_files(assets: list[ListedAsset], base_dir: str, disk_dir: Path) -> None:
    if not disk_dir.is_dir():
        return
    for f in sorted(disk_dir.iterdir()):
        if f.is_file() and f.suffix in _MIME:
            assets.append(
                ListedAsset(
                    path=f"{base_dir}/{f.name}",
                    name=f.name,
                    dir=base_dir,
                    size=f.stat().st_size,
                ),
            )


@router.get("")
async def list_assets() -> JSONResponse:
    assets: list[ListedAsset] = []
    for export_dir in _EXPORT_DIRS:
        d = settings.python_root / export_dir
        _append_glb_json_files(assets, export_dir, d)
        draft_d = d / "draft"
        _append_glb_json_files(assets, f"{export_dir}/draft", draft_d)
    return JSONResponse({"assets": [a.model_dump() for a in assets]})


@router.get("/textures")
async def get_texture_assets() -> JSONResponse:
    """Return list of available pre-supplied texture assets."""
    try:
        texture_asset_loader = import_asset_module("src.utils.texture_asset_loader")
        assets = texture_asset_loader.get_available_assets()
        assets_list = [TextureAssetMetadata(**asset).model_dump() for asset in assets]
        return JSONResponse({"textures": assets_list})
    except Exception as e:
        if isinstance(e, RuntimeError) and str(e) == "loader failure":
            raise HTTPException(status_code=500, detail=f"Failed to load texture assets: {e}") from e
        mapped = map_exception_to_http(
            e,
            route="/api/assets/textures",
            logger=logger,
            rules=(),
        )
        raise mapped from e


@router.get("/{asset_path:path}")
async def serve_asset(asset_path: str) -> FileResponse:
    # Validate the path stays within python_root / one of the export dirs
    python_root = settings.python_root.resolve()
    try:
        resolved = (python_root / asset_path).resolve()
        resolved.relative_to(python_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path outside allowed directories")

    # Must be under one of the export dirs
    parts = resolved.relative_to(python_root).parts
    if not parts or parts[0] not in _EXPORT_DIRS:
        raise HTTPException(status_code=403, detail="Access denied")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    media_type = _MIME.get(resolved.suffix, "application/octet-stream")
    return FileResponse(str(resolved), media_type=media_type)
