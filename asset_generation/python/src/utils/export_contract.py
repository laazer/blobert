"""
Export directory contract constants.

Canonical source for all export directory names used across:
- API routers (assets, registry)
- Python service modules (run_contract, config)
- Model registry validation

Consolidated from:
- src.utils.config.ExportConfig (STATIC_DIR, ANIMATED_DIR, PLAYER_DIR, LEVEL_DIR)
- asset_generation/web/backend/routers/assets._EXPORT_DIRS
"""

from __future__ import annotations

# Export directory roots - must match ExportConfig in config.py exactly
EXPORT_DIR_ROOTS: tuple[str, ...] = (
    "animated_exports",
    "exports",
    "player_exports",
    "level_exports",
)

# Draft subdirectory suffix for all export types
DRAFT_SUBDIR_SUFFIX: str = "draft"


def get_export_dirs_with_drafts() -> list[str]:
    """Return list of all export directories including draft variants."""
    dirs: list[str] = []
    for root in EXPORT_DIR_ROOTS:
        dirs.append(root)
        dirs.append(f"{root}/{DRAFT_SUBDIR_SUFFIX}")
    return dirs


def is_valid_export_path(path: str) -> bool:
    """Check if path starts with a valid export directory."""
    parts = path.split("/")
    if not parts:
        return False
    return parts[0] in EXPORT_DIR_ROOTS
