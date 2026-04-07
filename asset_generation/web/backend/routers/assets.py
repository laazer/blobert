from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from core.config import settings

router = APIRouter(prefix="/api/assets", tags=["assets"])

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


@router.get("")
async def list_assets() -> JSONResponse:
    assets: list[dict] = []
    for export_dir in _EXPORT_DIRS:
        d = settings.python_root / export_dir
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix in _MIME:
                assets.append({
                    "path": f"{export_dir}/{f.name}",
                    "name": f.name,
                    "dir": export_dir,
                    "size": f.stat().st_size,
                })
    return JSONResponse({"assets": assets})


@router.get("/{asset_path:path}")
async def serve_asset(asset_path: str) -> FileResponse:
    # Validate the path stays within python_root / one of the export dirs
    python_root = settings.python_root.resolve()
    resolved = (python_root / asset_path).resolve()
    try:
        resolved.relative_to(python_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path outside allowed directories")

    # Must be under one of the export dirs
    parts = resolved.relative_to(python_root).parts
    if not parts or parts[0] not in _EXPORT_DIRS:
        raise HTTPException(status_code=403, detail="Access denied")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Asset not found")

    media_type = _MIME.get(resolved.suffix, "application/octet-stream")
    return FileResponse(str(resolved), media_type=media_type)
