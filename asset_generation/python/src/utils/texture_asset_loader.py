"""Texture asset loading and validation for pre-supplied texture resources."""

import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlparse

# Do not import PIL at module load. generator.py runs under Blender's bundled
# Python (not the project venv); only `load_texture_image` needs Pillow.


def get_texture_assets_dir() -> Path:
    """Return the path to the texture assets directory."""
    return Path(__file__).parent.parent.parent.parent / "resources" / "textures"


def load_texture_manifest() -> dict[str, Any]:
    """Load the TEXTURES.json manifest file.

    Raises FileNotFoundError if manifest does not exist.
    Raises json.JSONDecodeError if manifest is invalid JSON.
    """
    manifest_path = get_texture_assets_dir() / "TEXTURES.json"
    with open(manifest_path) as f:
        return json.load(f)


def get_available_assets() -> list[dict[str, Any]]:
    """Return list of available texture assets with metadata."""
    manifest = load_texture_manifest()
    assets = []
    for asset_id, metadata in manifest.items():
        asset = {"id": asset_id}
        asset.update(metadata)
        assets.append(asset)
    return assets


def get_asset_metadata(asset_id: str) -> Optional[dict[str, Any]]:
    """Get metadata for a specific asset by ID.

    Returns None if asset does not exist.
    """
    manifest = load_texture_manifest()
    return manifest.get(asset_id)


def load_texture_image(asset_id: str) -> Any:
    """Load a texture image by asset ID (requires Pillow in the active interpreter).

    Raises ValueError if asset_id does not exist or file is missing.
    Raises IOError if image cannot be loaded.
    Raises ModuleNotFoundError if Pillow is not installed (e.g. non-Blender uv venv without sync).
    """
    from PIL import Image

    metadata = get_asset_metadata(asset_id)
    if not metadata:
        raise ValueError(f"Texture asset not found: {asset_id}")

    texture_path = get_texture_assets_dir() / metadata["filename"]
    if not texture_path.exists():
        raise IOError(f"Texture file not found: {texture_path}")

    return Image.open(texture_path)


def get_texture_asset_filepath(asset_id: str) -> Path:
    """Get the file path for a texture asset.

    Raises ValueError if asset_id does not exist.
    """
    metadata = get_asset_metadata(asset_id)
    if not metadata:
        raise ValueError(f"Texture asset not found: {asset_id}")

    return get_texture_assets_dir() / metadata["filename"]


def infer_texture_asset_id_from_preview(preview: str | None) -> Optional[str]:
    """Infer texture asset ID from a preview URL/path when ID is unavailable.

    Supports frontend preview shapes such as:
    - /api/assets/textures/file/demo%20textures3.png
    - http://localhost:8000/api/assets/textures/file/demo%20textures3.png
    - raw filename
    """
    if not preview:
        return None
    raw = str(preview).strip()
    if not raw:
        return None

    candidate = unquote(raw)
    parsed = urlparse(candidate)
    path = parsed.path if parsed.path else candidate
    filename = Path(path).name
    if not filename:
        return None

    manifest = load_texture_manifest()
    for asset_id, metadata in manifest.items():
        if not isinstance(metadata, dict):
            continue
        mf = str(metadata.get("filename", ""))
        if mf and Path(mf).name == filename:
            return str(asset_id)
    return None
