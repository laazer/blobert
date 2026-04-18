"""Test asset texture application to materials (M25-05)."""

from __future__ import annotations

import unittest.mock as mock

import bpy
import pytest

from src.materials.material_system import (
    _material_for_asset_zone,
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
