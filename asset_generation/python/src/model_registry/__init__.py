"""Versioned model registry (MRVC): draft / in-use flags and manifest I/O."""

from .service import (
    default_migrated_manifest,
    load_effective_manifest,
    patch_enemy_version,
    patch_player_active_visual,
    save_manifest_atomic,
    spawn_eligible_paths,
    sync_discovered_animated_glb_versions,
    validate_manifest,
)

__all__ = [
    "default_migrated_manifest",
    "load_effective_manifest",
    "patch_enemy_version",
    "patch_player_active_visual",
    "save_manifest_atomic",
    "spawn_eligible_paths",
    "sync_discovered_animated_glb_versions",
    "validate_manifest",
]
