"""Test asset texture application to materials (M25-05)."""

from __future__ import annotations

import unittest.mock as mock

import bpy
import pytest

from src.materials import feature_zones as fz_mod
from src.materials.material_system import (
    _material_for_asset_zone,
    _material_for_color_image_zone,
    apply_zone_texture_pattern_overrides,
)


@pytest.fixture
def mock_blender_setup():
    """Mock Blender's bpy module for testing."""
    with mock.patch.object(bpy, "data") as mock_data, mock.patch.object(
        bpy, "types"
    ) as mock_types:
        yield mock_data, mock_types


def _create_mock_material(name: str = "test_mat") -> mock.MagicMock:
    """Create a mock Blender material."""
    mat = mock.MagicMock()
    mat.name = name
    mat.use_nodes = True
    mat.node_tree = mock.MagicMock()
    mat.node_tree.nodes = mock.MagicMock()
    mat.node_tree.links = mock.MagicMock()
    return mat


class _ColorImageZoneNodeBuilder:
    """Iterable node tree with ``.new()`` for color-image material tests."""

    def __init__(self, principled_nodes: list) -> None:
        self._items = principled_nodes
        self.new_types: list[str] = []

    def __iter__(self):
        return iter(self._items)

    def new(self, *, type: str):
        self.new_types.append(type)
        n = mock.MagicMock()
        n.outputs = {"UV": mock.MagicMock(), "Color": mock.MagicMock()}
        n.inputs = {"Vector": mock.MagicMock()}
        return n


def test_apply_zone_texture_pattern_overrides_none_mode() -> None:
    """Asset mode is skipped when mode is 'none'."""
    mat = _create_mock_material()
    options = {"feat_body_texture_mode": "none"}
    result = apply_zone_texture_pattern_overrides({"body": mat}, options)
    assert result["body"] == mat


def test_apply_zone_texture_pattern_overrides_asset_mode_no_asset_id() -> None:
    """Asset mode with empty asset_id returns original material."""
    mat = _create_mock_material()
    options = {"feat_body_texture_mode": "assets", "feat_body_texture_asset_id": ""}
    result = apply_zone_texture_pattern_overrides({"body": mat}, options)
    assert result["body"] == mat


def test_material_for_asset_zone_handles_missing_asset() -> None:
    """Asset zone material handles missing asset gracefully by returning copy."""
    mat = _create_mock_material()
    mat.copy.return_value = _create_mock_material()
    with mock.patch(
        "src.utils.texture_asset_loader.get_texture_asset_filepath",
        side_effect=ValueError("Asset not found"),
    ):
        result = _material_for_asset_zone(mat, "nonexistent", 1.0)
    assert "asset" in result.name.lower()


@mock.patch("src.materials.material_system.bpy.data.images")
@mock.patch("src.utils.texture_asset_loader.get_texture_asset_filepath")
def test_material_for_asset_zone_creates_copy(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
) -> None:
    """Asset zone material creates a copy of the base material."""
    from pathlib import Path

    mock_get_path.return_value = Path("/fake/texture.png")
    mock_image = mock.MagicMock()
    mock_images.load.return_value = mock_image

    mat = _create_mock_material("original")
    mat.copy.return_value = _create_mock_material("original_asset")

    result = _material_for_asset_zone(mat, "demo_textures3", 2.0)
    assert result.name == "original_asset"


@mock.patch("src.materials.material_system.bpy.data.images")
@mock.patch("src.utils.texture_asset_loader.get_texture_asset_filepath")
def test_apply_zone_texture_pattern_overrides_asset_mode_valid_asset(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
) -> None:
    """Asset mode with valid asset_id creates new material."""
    from pathlib import Path

    mock_get_path.return_value = Path("/fake/texture.png")
    mock_image = mock.MagicMock()
    mock_images.load.return_value = mock_image

    mat = _create_mock_material()
    mat.copy.return_value = _create_mock_material("copied")
    options = {
        "feat_body_texture_mode": "assets",
        "feat_body_texture_asset_id": "demo_textures3",
        "feat_body_texture_asset_tile_repeat": 2.0,
    }

    result = apply_zone_texture_pattern_overrides({"body": mat}, options)
    assert result["body"] is not None


@mock.patch("src.materials.material_system.bpy.data.images")
@mock.patch("src.utils.texture_asset_loader.get_texture_asset_filepath")
def test_material_for_color_image_zone_loads_file_and_wires_nodes(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
) -> None:
    """Covers _material_for_color_image_zone when a principled BSDF is present."""
    from pathlib import Path

    P = type("ShaderNodeBsdfPrincipled", (), {})
    p = P()
    p.type = "BSDF"
    p.inputs = {"Base Color": mock.MagicMock()}

    ns = _ColorImageZoneNodeBuilder([p])
    flinks = mock.MagicMock()
    flinks.new = mock.MagicMock()
    nt = mock.MagicMock()
    nt.nodes = ns
    nt.links = flinks

    copy_mat = mock.MagicMock()
    copy_mat.name = "base_color_img"
    copy_mat.use_nodes = True
    copy_mat.node_tree = nt

    base = mock.MagicMock()
    base.name = "base"
    base.use_nodes = True
    base.node_tree = nt
    base.copy.return_value = copy_mat

    mock_get_path.return_value = Path("/tmp/fake_color.png")
    mock_images.load.return_value = mock.MagicMock()

    with mock.patch("src.materials.material_system.bpy.types.ShaderNodeBsdfPrincipled", P):
        out = _material_for_color_image_zone(base, "demo_textures3")
    assert out is copy_mat
    mock_get_path.assert_called_once_with("demo_textures3")
    mock_images.load.assert_called_once()
    assert "ShaderNodeTexCoord" in ns.new_types
    assert "ShaderNodeTexImage" in ns.new_types
    assert flinks.new.call_count >= 2


@mock.patch("src.materials.material_system.bpy.data.images")
@mock.patch("src.utils.texture_asset_loader.get_texture_asset_filepath", side_effect=ValueError("missing"))
def test_material_for_color_image_zone_warns_on_load_error(
    _mock_images: mock.MagicMock,
    _get_path: mock.MagicMock,
) -> None:
    """Exception path in _material_for_color_image_zone still returns material copy."""
    P = type("ShaderNodeBsdfPrincipled", (), {})
    p = P()
    p.type = "BSDF"
    p.inputs = {"Base Color": mock.MagicMock()}
    ns = _ColorImageZoneNodeBuilder([p])
    flinks = mock.MagicMock()
    nt = mock.MagicMock()
    nt.nodes = ns
    nt.links = flinks
    copy_mat = mock.MagicMock()
    copy_mat.name = "b_ci"
    copy_mat.use_nodes = True
    copy_mat.node_tree = nt
    base = mock.MagicMock()
    base.name = "b"
    base.use_nodes = True
    base.node_tree = nt
    base.copy.return_value = copy_mat
    with mock.patch("src.materials.material_system.bpy.types.ShaderNodeBsdfPrincipled", P):
        out = _material_for_color_image_zone(base, "bad_id")
    assert out is copy_mat
    # No image load: load should not be called
    _mock_images.load.assert_not_called()


@mock.patch("src.materials.material_system.bpy.data.images")
@mock.patch("src.utils.texture_asset_loader.get_texture_asset_filepath")
def test_material_for_color_image_zone_returns_early_without_principled(
    _gp: mock.MagicMock,
    _mi: mock.MagicMock,
) -> None:
    class _Empty:
        def __iter__(self):
            return iter(())

    nt = mock.MagicMock()
    nt.nodes = _Empty()
    nt.links = mock.MagicMock()
    copy_mat = mock.MagicMock()
    copy_mat.name = "solo"
    copy_mat.use_nodes = True
    copy_mat.node_tree = nt
    base = mock.MagicMock()
    base.name = "solo"
    base.use_nodes = False
    base.node_tree = nt
    base.copy.return_value = copy_mat
    out = _material_for_color_image_zone(base, "any")
    assert copy_mat.use_nodes is True
    assert out is copy_mat
    _gp.assert_not_called()


@mock.patch("src.materials.feature_zones.bpy.data.images")
@mock.patch("src.materials.feature_zones.get_texture_asset_filepath")
def test_feature_zones_material_for_color_image_zone_loads_file(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
) -> None:
    """Covers feature_zones._material_for_color_image_zone (Blender path, not material_system)."""
    from pathlib import Path

    P = type("ShaderNodeBsdfPrincipled", (), {})
    p = P()
    p.type = "BSDF"
    p.inputs = {"Base Color": mock.MagicMock()}

    ns = _ColorImageZoneNodeBuilder([p])
    flinks = mock.MagicMock()
    flinks.new = mock.MagicMock()
    nt = mock.MagicMock()
    nt.nodes = ns
    nt.links = flinks

    copy_mat = mock.MagicMock()
    copy_mat.name = "base_color_img"
    copy_mat.use_nodes = True
    copy_mat.node_tree = nt

    base = mock.MagicMock()
    base.name = "base"
    base.use_nodes = True
    base.node_tree = nt
    base.copy.return_value = copy_mat

    mock_get_path.return_value = Path("/tmp/fake_color_fz.png")
    mock_images.load.return_value = mock.MagicMock()

    with mock.patch("src.materials.feature_zones.bpy.types.ShaderNodeBsdfPrincipled", P):
        out = fz_mod._material_for_color_image_zone(base, "demo_textures3")
    assert out is copy_mat
    mock_get_path.assert_called_once_with("demo_textures3")
    mock_images.load.assert_called_once()
    assert "ShaderNodeTexCoord" in ns.new_types
