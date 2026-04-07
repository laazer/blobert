"""
Canonical stems for GLB exports (no file I/O).

Animated enemy files use `{enemy_type}_animated_{variant:02d}.glb` in ``ExportConfig.ANIMATED_DIR``.
Prefab runs insert `_prefab_{name}` before the variant index.

Keep in sync with:
  - ``ExportConfig.ANIMATED_PATTERN`` (full filename with format extension)
  - Godot ``EnemyNameUtils`` / asset family extraction
  - Web ``glbVariants.parseVariantFilename`` (trailing ``_NN.glb``)
"""

from __future__ import annotations


def animated_export_stem(enemy_type: str, variant_index: int, *, prefab_name: str | None = None) -> str:
    """Return filename stem (no ``.glb``) for one animated export variant."""
    if prefab_name:
        return f"{enemy_type}_animated_prefab_{prefab_name}_{variant_index:02d}"
    return f"{enemy_type}_animated_{variant_index:02d}"
