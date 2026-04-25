"""Verify export paths invoke procedural stripe bake compatibility pass."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

sys.modules.setdefault("bpy", MagicMock())
sys.modules.setdefault("mathutils", MagicMock())


def _prepare_common_bpy_state() -> None:
    import bpy  # type: ignore[import-not-found]

    bpy.ops.object.mode_set.return_value = None
    bpy.ops.object.select_all.return_value = None
    bpy.ops.export_scene.gltf.return_value = None
    bpy.ops.wm.save_as_mainfile.return_value = None
    bpy.context.view_layer.objects.active = None


def test_export_enemy_calls_bake_hook(tmp_path) -> None:
    _prepare_common_bpy_state()
    from src.enemies.base_enemy import export_enemy

    armature = MagicMock()
    armature.animation_data = MagicMock()
    armature.animation_data.action = None
    mesh = MagicMock()
    mesh.select_set = MagicMock()

    with patch("src.enemies.base_enemy.bake_procedural_stripes_for_export") as mock_bake:
        export_enemy(armature, mesh, "enemy", str(tmp_path))
        mock_bake.assert_called_once_with(mesh, str(tmp_path))


def test_export_enemy_bakes_before_final_selection(tmp_path) -> None:
    _prepare_common_bpy_state()
    from src.enemies.base_enemy import export_enemy

    armature = MagicMock()
    armature.animation_data = MagicMock()
    armature.animation_data.action = None
    mesh = MagicMock()
    order: list[str] = []
    armature.select_set.side_effect = lambda _state: order.append("armature_selected")
    mesh.select_set.side_effect = lambda _state: order.append("mesh_selected")

    with patch("src.enemies.base_enemy.bake_procedural_stripes_for_export") as mock_bake:
        mock_bake.side_effect = lambda _mesh, _dir: order.append("baked")
        export_enemy(armature, mesh, "enemy", str(tmp_path))
        assert order.index("baked") < order.index("armature_selected")
        assert order.index("baked") < order.index("mesh_selected")


def test_export_player_calls_bake_hook(tmp_path) -> None:
    _prepare_common_bpy_state()
    from src.player.player_builder import export_player_slime

    armature = MagicMock()
    armature.select_set = MagicMock()
    mesh = MagicMock()
    mesh.select_set = MagicMock()

    with patch("src.player.player_builder.bake_procedural_stripes_for_export") as mock_bake:
        export_player_slime(armature, mesh, "player", str(tmp_path))
        mock_bake.assert_called_once_with(mesh, str(tmp_path))


def test_export_player_bakes_before_final_selection(tmp_path) -> None:
    _prepare_common_bpy_state()
    from src.player.player_builder import export_player_slime

    armature = MagicMock()
    mesh = MagicMock()
    order: list[str] = []
    armature.select_set.side_effect = lambda _state: order.append("armature_selected")
    mesh.select_set.side_effect = lambda _state: order.append("mesh_selected")

    with patch("src.player.player_builder.bake_procedural_stripes_for_export") as mock_bake:
        mock_bake.side_effect = lambda _mesh, _dir: order.append("baked")
        export_player_slime(armature, mesh, "player", str(tmp_path))
        assert order.index("baked") < order.index("armature_selected")
        assert order.index("baked") < order.index("mesh_selected")


def test_export_level_object_calls_bake_hook(tmp_path) -> None:
    _prepare_common_bpy_state()
    from src.level.base_level_object import export_level_object

    mesh = MagicMock()
    mesh.select_set = MagicMock()

    with patch("src.level.base_level_object.bake_procedural_stripes_for_export") as mock_bake:
        export_level_object(mesh, "platform", str(tmp_path))
        mock_bake.assert_called_once_with(mesh, str(tmp_path))
