"""
Post-export / post-run registry snapshot attach helper (FEAT-20260522).

Spec: R3, R5 — service helper persists ``build_options`` on the version row for a GLB path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.model_registry.service import (
    default_migrated_manifest,
    load_effective_manifest,
    save_manifest_atomic,
)
from src.utils.build_options import (
    coerce_validate_enemy_build_options,
    options_for_enemy,
)


def _attach_helper():
    import src.model_registry.service as svc

    fn = getattr(svc, "attach_build_options_to_version_by_path", None)
    if fn is None:
        pytest.fail("attach_build_options_to_version_by_path is not implemented on model_registry.service")
    return fn


def test_attach_build_options_to_version_by_path_persists_on_enemy_row(tmp_path: Path) -> None:
    attach_build_options_to_version_by_path = _attach_helper()
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    snap = coerce_validate_enemy_build_options("spider", options_for_enemy("spider", {"eye_count": 7}))
    path = "animated_exports/spider_animated_00.glb"

    attach_build_options_to_version_by_path(tmp_path, path, snap)

    row = next(
        r
        for r in load_effective_manifest(tmp_path)["enemies"]["spider"]["versions"]
        if r["path"] == path
    )
    assert row["build_options"]["eye_count"] == 7


def test_attach_build_options_to_version_by_path_unknown_path_raises(tmp_path: Path) -> None:
    attach_build_options_to_version_by_path = _attach_helper()
    save_manifest_atomic(tmp_path, default_migrated_manifest())
    snap = coerce_validate_enemy_build_options("imp", options_for_enemy("imp", {}))
    with pytest.raises(KeyError, match="unknown"):
        attach_build_options_to_version_by_path(
            tmp_path,
            "animated_exports/missing.glb",
            snap,
        )
