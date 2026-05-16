"""Exercise generator + animated_pipeline export paths under mocks (diff-cover)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _ensure_bpy_stub() -> None:
    sys.modules.setdefault("bpy", MagicMock())


def test_generate_animated_enemy_passes_build_options_snapshot_to_export(tmp_path: Path) -> None:
    from src import generator as gen

    built = MagicMock()
    built.armature = MagicMock()
    built.mesh = MagicMock()
    built.attack_profile = []

    export_dir = str(tmp_path / "out")
    Path(export_dir).mkdir()

    with (
        patch.object(gen, "clear_scene"),
        patch.object(gen, "setup_scene"),
        patch.object(gen, "setup_materials", return_value={}),
        patch.object(gen, "variant_start_index", return_value=0),
        patch.object(gen, "load_prefab_mesh_if_requested", return_value=None),
        patch.object(gen.AnimatedEnemyBuilder, "create_enemy", return_value=built),
        patch.object(gen, "animated_export_stem", return_value="enemy_00"),
        patch.object(gen, "_build_options_for_current_enemy", return_value={"k": "v"}),
        patch.object(gen, "export_enemy") as ex,
    ):
        gen.generate_animated_enemy("slug", count=1, export_dir=export_dir)

    ex.assert_called_once()
    kwargs = ex.call_args.kwargs
    assert kwargs.get("build_options_snapshot") == {"k": "v"}


def test_run_blueprint_export_in_blender_exports_when_mesh_ready(tmp_path: Path) -> None:
    from src.enemies import animated_pipeline as ap

    built = MagicMock()
    built.armature = MagicMock()
    built.mesh = MagicMock()
    built.attack_profile = []

    export_dir = str(tmp_path / "bp")
    Path(export_dir).mkdir()

    with (
        patch.object(ap, "clear_scene"),
        patch.object(ap, "setup_materials", return_value={}),
        patch.object(ap.AnimatedEnemyBuilder, "create_enemy", return_value=built),
        patch.object(ap, "options_for_enemy", return_value={"a": 1}),
        patch.object(ap, "export_enemy") as ex,
    ):
        ok = ap.run_blueprint_export_in_blender("bp_slug", "slug", 7, export_dir)

    assert ok is True
    ex.assert_called_once()
    assert ex.call_args.kwargs.get("build_options_snapshot") == {"a": 1}
