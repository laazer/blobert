"""Export naming, directory helpers, and GLB path validation for the asset pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from src.utils.config import ExportConfig, LevelExportConfig, PlayerExportConfig

_EXPORT_USE_DRAFT_ENV = "BLOBERT_EXPORT_USE_DRAFT_SUBDIR"
_EXPORT_START_INDEX_ENV = "BLOBERT_EXPORT_START_INDEX"
_DRAFT = "draft"


def animated_export_stem(
    enemy_type: str,
    variant_index: int,
    *,
    prefab_name: str | None = None,
) -> str:
    """Return filename stem (no ``.glb``) for one animated export variant."""
    if prefab_name:
        return f"{enemy_type}_animated_prefab_{prefab_name}_{variant_index:02d}"
    return f"{enemy_type}_animated_{variant_index:02d}"


def _use_draft_subdir() -> bool:
    return os.environ.get(_EXPORT_USE_DRAFT_ENV) == "1"


def variant_start_index() -> int:
    """Starting variant index for this export run (``BLOBERT_EXPORT_START_INDEX``)."""
    val = os.environ.get(_EXPORT_START_INDEX_ENV)
    if val is not None:
        try:
            return max(0, int(val))
        except ValueError:
            pass
    return 0


def animated_export_directory() -> str:
    base = ExportConfig.ANIMATED_DIR
    if _use_draft_subdir():
        return os.path.join(base, _DRAFT)
    return base


def player_export_directory() -> str:
    base = PlayerExportConfig.PLAYER_DIR
    if _use_draft_subdir():
        return os.path.join(base, _DRAFT)
    return base


def level_export_directory() -> str:
    base = LevelExportConfig.LEVEL_DIR
    if _use_draft_subdir():
        return os.path.join(base, _DRAFT)
    return base


def validate_glb_path(path: str | os.PathLike[str]) -> Path:
    """Return a resolved Path to an existing non-empty ``.glb`` file, or raise ``ValueError``."""
    if isinstance(path, str) and not path.strip():
        raise ValueError("GLB path is empty")
    p = Path(path).expanduser()
    try:
        resolved = p.resolve(strict=True)
    except FileNotFoundError as e:
        raise ValueError(f"GLB path is not a readable file: {p}") from e
    except OSError as e:
        raise ValueError(f"GLB path is not a readable file: {p}") from e
    if not resolved.is_file():
        raise ValueError(f"GLB path is not a file: {resolved}")
    if resolved.suffix.lower() != ".glb":
        raise ValueError(f"Not a .glb file: {resolved}")
    if resolved.stat().st_size == 0:
        raise ValueError(f"GLB file is empty: {resolved}")
    return resolved
