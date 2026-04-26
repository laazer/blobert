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


def _get_export_dirs() -> list[str]:
    """Get export directory roots from canonical contract module."""
    try:
        contract_module = import_asset_module("src.utils.export_contract")
        return list(contract_module.EXPORT_DIR_ROOTS)
    except ImportError as e:
        logger.warning(
            "assets: fallback to hardcoded export dirs — %s", e, exc_info=True
        )
        # Hardcoded fallback (should match canonical order)
        return [
            "animated_exports",
            "exports",
            "player_exports",
            "level_exports",
        ]


def _is_valid_export_path(path: str) -> bool:
    """Check if path starts with a valid export directory."""
    try:
        contract_module = import_asset_module("src.utils.export_contract")
        return contract_module.is_valid_export_path(path)
    except ImportError as e:
        logger.warning(
            "assets: fallback to hardcoded validation — %s", e, exc_info=True
        )
        # Hardcoded fallback (should match canonical order)
        valid_dirs = [
            "animated_exports",
            "exports",
            "player_exports",
            "level_exports",
        ]
        parts = path.split("/")
        if not parts:
            return False
        return parts[0] in valid_dirs

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
    url: str | None = None


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
    export_dirs = _get_export_dirs()
    for export_dir in export_dirs:
        d = settings.python_root / export_dir
        _append_glb_json_files(assets, export_dir, d)
        draft_d = d / "draft"
        _append_glb_json_files(assets, f"{export_dir}/draft", draft_d)
    return JSONResponse({"assets": [a.model_dump() for a in assets]})


@router.get("/textures")
async def get_texture_assets() -> JSONResponse:
    """Return list of available pre-supplied texture assets with URLs."""
    try:
        texture_asset_loader = import_asset_module("src.utils.texture_asset_loader")
        assets = texture_asset_loader.get_available_assets()
        assets_list = []
        for asset in assets:
            meta = TextureAssetMetadata(**asset)
            # Construct URL using encoded filename to avoid path traversal issues
            encoded_filename = "/".join(p.replace(" ", "%20") for p in meta.filename.split("/"))
            meta_dict = meta.model_dump()
            meta_dict["url"] = f"/api/assets/textures/file/{encoded_filename}"
            assets_list.append(meta_dict)
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


@router.get("/textures/file/{file_path:path}")
async def serve_texture_file(file_path: str) -> FileResponse:
    """Serve a texture file by relative path from resources/textures/."""
    try:
        texture_asset_loader = import_asset_module("src.utils.texture_asset_loader")
        # Decode URL-encoded filename and validate it exists in texture assets
        import urllib.parse
        decoded_path = urllib.parse.unquote(file_path)

        # Get the texture directory and construct the full path
        texture_dir = texture_asset_loader.get_texture_assets_dir()
        full_path = (texture_dir / decoded_path).resolve()

        # Ensure path is within texture directory (prevent traversal)
        full_path.relative_to(texture_dir)

        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="Texture file not found")

        return FileResponse(
            full_path,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied - path outside texture directory")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error("Error serving texture file %s: %s", file_path, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to serve texture file") from e


@router.get("/{asset_path:path}")
async def serve_asset(asset_path: str) -> FileResponse:
    # Validate the path stays within python_root / one of the export dirs
    python_root = settings.python_root.resolve()
    try:
        resolved = (python_root / asset_path).resolve()
        resolved.relative_to(python_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path outside allowed directories")

    # Must be under one of the export dirs - use canonical validation
    if not _is_valid_export_path(asset_path):
        raise HTTPException(status_code=403, detail="Access denied")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    media_type = _MIME.get(resolved.suffix, "application/octet-stream")
    return FileResponse(str(resolved), media_type=media_type)
