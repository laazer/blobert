"""Integration tests for checkerboard texture mode wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@patch("src.materials.material_system.bpy")
def test_checkerboard_mode_calls_checkerboard_factory(mock_bpy) -> None:  # noqa: ARG001
    from src.materials.material_system import apply_zone_texture_pattern_overrides

    mock_mat = MagicMock()
    slot_materials = {"body": mock_mat}
    build_options = {
        "feat_body_texture_mode": "checkerboard",
        "feat_body_texture_spot_color": "ff0000",
        "feat_body_texture_spot_bg_color": "ffffff",
        "feat_body_texture_spot_density": 1.5,
        "features": {"body": {"hex": "cccccc", "finish": "default"}},
    }

    with patch("src.materials.material_system._material_for_checkerboard_zone") as mock_factory:
        mock_factory.return_value = mock_mat
        with patch("src.materials.material_system._palette_base_name_from_material") as mock_palette:
            mock_palette.return_value = "test_palette"
            apply_zone_texture_pattern_overrides(slot_materials, build_options)
            mock_factory.assert_called_once()
            kw = mock_factory.call_args.kwargs
            assert kw.get("base_palette_name") == "test_palette"
            assert kw.get("color_a_hex") == "ff0000"
            assert kw.get("color_b_hex") == "ffffff"
            assert kw.get("density") == pytest.approx(1.5)


@patch("src.materials.material_system.create_material")
@patch("src.materials.material_system.MaterialColors")
def test_material_for_checkerboard_zone_creates_material_with_nodes(
    mock_colors, mock_create
) -> None:
    from src.materials.material_system import _material_for_checkerboard_zone

    mock_colors.get_all.return_value = {"test": (0.5, 0.5, 0.5, 1.0)}
    mock_mat = MagicMock()
    mock_mat.node_tree = None
    mock_create.return_value = mock_mat

    result = _material_for_checkerboard_zone(
        base_palette_name="test",
        finish="default",
        color_a_hex="ff0000",
        color_b_hex="00ff00",
        density=1.0,
        zone_hex_fallback="0000ff",
        instance_suffix="test_zone",
    )

    assert result == mock_mat
    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["name"] == "test__feat_test_zone"
    assert call_kwargs["add_texture"] is False


@patch("src.materials.material_system.create_material")
@patch("src.materials.material_system._find_principled_bsdf")
@patch("src.materials.material_system._principled_base_color_socket")
@patch("src.materials.material_system.MaterialColors")
def test_material_for_checkerboard_zone_builds_node_tree(
    mock_colors, mock_bc_socket, mock_find_bsdf, mock_create
) -> None:
    from src.materials.material_system import _material_for_checkerboard_zone

    mock_colors.get_all.return_value = {"test": (0.5, 0.5, 0.5, 1.0)}

    bc_in = MagicMock()
    bc_in.links = []
    mock_bc_socket.return_value = bc_in
    mock_bsdf = MagicMock()
    mock_find_bsdf.return_value = mock_bsdf

    class _FakeNodes:
        def new(self, *, type):
            return MagicMock()

    class _FakeLinks:
        def __init__(self):
            self.new_calls = []
            self.removed = []

        def new(self, *args):
            self.new_calls.append(args)

        def remove(self, lk):
            self.removed.append(lk)

    nodes = _FakeNodes()
    links = _FakeLinks()
    nt = MagicMock()
    nt.nodes = nodes
    nt.links = links
    mock_mat = MagicMock()
    mock_mat.node_tree = nt
    mock_create.return_value = mock_mat

    result = _material_for_checkerboard_zone(
        base_palette_name="test",
        finish="default",
        color_a_hex="ff0000",
        color_b_hex="00ff00",
        density=1.0,
        zone_hex_fallback="0000ff",
        instance_suffix="test_zone",
    )

    assert result == mock_mat
    assert mock_mat.__setitem__.called
    mock_mat.__setitem__.assert_called_with("blobert_checker_procedural", True)
    assert len(links.new_calls) == 3


@patch("src.materials.material_system.ENEMY_FINISH_PRESETS", {"glossy": (0.3, 0.5, 0.8), "default": (0.7, None, 0.0)})
@patch("src.materials.material_system.create_material")
@patch("src.materials.material_system._find_principled_bsdf")
@patch("src.materials.material_system._principled_base_color_socket")
@patch("src.materials.material_system.MaterialColors")
def test_material_for_checkerboard_zone_with_missing_palette_and_custom_finish(
    mock_colors, mock_bc_socket, mock_find_bsdf, mock_create
) -> None:
    from src.materials.material_system import _material_for_checkerboard_zone

    mock_colors.get_all.return_value = {}

    bc_in = MagicMock()
    existing_link = MagicMock()
    bc_in.links = [existing_link]
    mock_bc_socket.return_value = bc_in
    mock_bsdf = MagicMock()
    mock_find_bsdf.return_value = mock_bsdf

    class _FakeNodes:
        def new(self, *, type):
            return MagicMock()

    class _FakeLinks:
        def __init__(self):
            self.new_calls = []
            self.removed = []

        def new(self, *args):
            self.new_calls.append(args)

        def remove(self, lk):
            self.removed.append(lk)

    nodes = _FakeNodes()
    links = _FakeLinks()
    nt = MagicMock()
    nt.nodes = nodes
    nt.links = links
    mock_mat = MagicMock()
    mock_mat.node_tree = nt
    mock_create.return_value = mock_mat

    result = _material_for_checkerboard_zone(
        base_palette_name="missing",
        finish="glossy",
        color_a_hex="ff0000",
        color_b_hex="00ff00",
        density=1.0,
        zone_hex_fallback="0000ff",
        instance_suffix="test_zone",
    )

    assert result == mock_mat
    assert len(links.removed) == 1
    assert existing_link in links.removed
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["roughness"] == 0.3
