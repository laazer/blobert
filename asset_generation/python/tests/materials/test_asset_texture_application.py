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


@pytest.mark.parametrize("node_type", ["BSDF", "BSDF_PRINCIPLED"])
@mock.patch("src.materials.material_system.bpy.data.images")
@mock.patch("src.utils.texture_asset_loader.get_texture_asset_filepath")
def test_material_for_color_image_zone_loads_file_and_wires_nodes(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
    node_type: str,
) -> None:
    """Color-image wiring works for both Principled node type spellings."""
    from pathlib import Path

    P = type("ShaderNodeBsdfPrincipled", (), {})
    p = P()
    p.type = node_type
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
    p.type = "BSDF_PRINCIPLED"
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


@pytest.mark.parametrize("node_type", ["BSDF", "BSDF_PRINCIPLED"])
@mock.patch("src.materials.feature_zones.bpy.data.images")
@mock.patch("src.materials.feature_zones.get_texture_asset_filepath")
def test_feature_zones_material_for_color_image_zone_loads_file(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
    node_type: str,
) -> None:
    """feature_zones helper accepts both Principled node type variants."""
    from pathlib import Path

    P = type("ShaderNodeBsdfPrincipled", (), {})
    p = P()
    p.type = node_type
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


@pytest.mark.parametrize("node_type", ["BSDF", "BSDF_PRINCIPLED"])
@mock.patch("src.materials.material_system.bpy.data.images")
@mock.patch("src.utils.texture_asset_loader.get_texture_asset_filepath")
def test_material_system_asset_zone_supports_principled_node_variants(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
    node_type: str,
) -> None:
    from pathlib import Path

    P = type("ShaderNodeBsdfPrincipled", (), {})
    p = P()
    p.type = node_type
    p.inputs = {"Base Color": mock.MagicMock()}

    ns = _ColorImageZoneNodeBuilder([p])
    flinks = mock.MagicMock()
    flinks.new = mock.MagicMock()
    nt = mock.MagicMock()
    nt.nodes = ns
    nt.links = flinks

    copy_mat = mock.MagicMock()
    copy_mat.name = "base_asset"
    copy_mat.use_nodes = True
    copy_mat.node_tree = nt

    base = mock.MagicMock()
    base.name = "base"
    base.use_nodes = True
    base.node_tree = nt
    base.copy.return_value = copy_mat

    mock_get_path.return_value = Path("/tmp/fake_asset.png")
    mock_images.load.return_value = mock.MagicMock()

    with mock.patch("src.materials.material_system.bpy.types.ShaderNodeBsdfPrincipled", P):
        out = _material_for_asset_zone(base, "demo_textures3", 1.0)
    assert out is copy_mat
    mock_get_path.assert_called_once_with("demo_textures3")
    mock_images.load.assert_called_once()
    assert "ShaderNodeTexCoord" in ns.new_types
    assert "ShaderNodeTexImage" in ns.new_types


@pytest.mark.parametrize("node_type", ["BSDF", "BSDF_PRINCIPLED"])
@mock.patch("src.materials.feature_zones.bpy.data.images")
@mock.patch("src.materials.feature_zones.get_texture_asset_filepath")
def test_feature_zones_asset_zone_supports_principled_node_variants(
    mock_get_path: mock.MagicMock,
    mock_images: mock.MagicMock,
    node_type: str,
) -> None:
    from pathlib import Path

    P = type("ShaderNodeBsdfPrincipled", (), {})
    p = P()
    p.type = node_type
    p.inputs = {"Base Color": mock.MagicMock()}

    ns = _ColorImageZoneNodeBuilder([p])
    flinks = mock.MagicMock()
    flinks.new = mock.MagicMock()
    nt = mock.MagicMock()
    nt.nodes = ns
    nt.links = flinks

    copy_mat = mock.MagicMock()
    copy_mat.name = "base_asset_fz"
    copy_mat.use_nodes = True
    copy_mat.node_tree = nt

    base = mock.MagicMock()
    base.name = "base"
    base.use_nodes = True
    base.node_tree = nt
    base.copy.return_value = copy_mat

    mock_get_path.return_value = Path("/tmp/fake_asset_fz.png")
    mock_images.load.return_value = mock.MagicMock()

    with mock.patch("src.materials.feature_zones.bpy.types.ShaderNodeBsdfPrincipled", P):
        out = fz_mod._material_for_asset_zone(base, "demo_textures3", 1.0)
    assert out is copy_mat
    mock_get_path.assert_called_once_with("demo_textures3")
    mock_images.load.assert_called_once()
    assert "ShaderNodeTexCoord" in ns.new_types
    assert "ShaderNodeTexImage" in ns.new_types


@mock.patch("src.materials.material_system._material_for_asset_zone")
def test_pattern_spots_image_mode_uses_asset_material_material_system(
    mock_asset: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    asset_mat = _create_mock_material("asset_mat")
    mock_asset.return_value = asset_mat
    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_color_mode": "image",
            "feat_body_texture_spot_color_image_id": "demo_textures3",
            "feat_body_texture_asset_tile_repeat": 2.0,
        },
    )
    assert out["body"] is asset_mat
    assert mock_asset.call_args.kwargs["asset_id"] == "demo_textures3"
    assert mock_asset.call_args.kwargs["tile_repeat"] == 2.0


@mock.patch("src.materials.feature_zones._material_for_asset_zone")
def test_feature_zones_apply_zone_texture_assets_mode(
    mock_asset: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    asset_mat = _create_mock_material("asset_mat")
    mock_asset.return_value = asset_mat
    out = fz_mod.apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "assets",
            "feat_body_texture_asset_id": "demo_textures3",
            "feat_body_texture_asset_tile_repeat": 2.0,
        },
    )
    assert out["body"] is asset_mat
    assert mock_asset.call_args.kwargs["asset_id"] == "demo_textures3"
    assert mock_asset.call_args.kwargs["tile_repeat"] == 2.0


@mock.patch("src.materials.feature_zones._material_for_asset_zone")
def test_feature_zones_spots_image_mode_uses_asset_material(
    mock_asset: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    asset_mat = _create_mock_material("asset_mat")
    mock_asset.return_value = asset_mat
    out = fz_mod.apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_color_mode": "image",
            "feat_body_texture_spot_color_image_id": "demo_textures3",
            "feat_body_texture_asset_tile_repeat": 1.75,
        },
    )
    assert out["body"] is asset_mat
    assert mock_asset.call_args.kwargs["asset_id"] == "demo_textures3"


@mock.patch("src.materials.feature_zones._material_for_asset_zone")
def test_pattern_stripes_image_mode_uses_asset_material_feature_zones(
    mock_asset: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    asset_mat = _create_mock_material("asset_mat")
    mock_asset.return_value = asset_mat
    out = fz_mod.apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "stripes",
            "feat_body_texture_stripe_bg_color_mode": "image",
            "feat_body_texture_stripe_bg_color_image_id": "demo_textures34",
            "feat_body_texture_asset_tile_repeat": 1.5,
        },
    )
    assert out["body"] is asset_mat
    assert mock_asset.call_args.kwargs["asset_id"] == "demo_textures34"
    assert mock_asset.call_args.kwargs["tile_repeat"] == 1.5


@mock.patch("src.materials.material_system._material_for_asset_zone")
def test_pattern_image_selection_prefers_foreground_over_background(
    mock_asset: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    asset_mat = _create_mock_material("asset_mat")
    mock_asset.return_value = asset_mat
    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_color_mode": "image",
            "feat_body_texture_spot_color_image_id": "foreground_img",
            "feat_body_texture_spot_bg_color_mode": "image",
            "feat_body_texture_spot_bg_color_image_id": "background_img",
        },
    )
    assert out["body"] is asset_mat
    assert mock_asset.call_args.kwargs["asset_id"] == "foreground_img"


@mock.patch("src.materials.material_system.material_for_spots_zone")
@mock.patch("src.materials.material_system._material_for_asset_zone")
def test_pattern_non_image_mode_uses_color_keys_not_image_ids(
    mock_asset: mock.MagicMock,
    mock_spots: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    spots_mat = _create_mock_material("spots_mat")
    mock_spots.return_value = spots_mat
    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_color_mode": "single",
            "feat_body_texture_spot_color_image_id": "should_not_be_used",
            "feat_body_texture_spot_color": "ff00ff",
            "feat_body_texture_spot_bg_color": "00ffff",
            "feat_body_texture_spot_density": 2.0,
        },
    )
    assert out["body"] is spots_mat
    mock_asset.assert_not_called()
    assert mock_spots.call_args.kwargs["spot_hex"] == "ff00ff"
    assert mock_spots.call_args.kwargs["bg_hex"] == "00ffff"


@mock.patch("src.materials.material_system._material_for_checkerboard_zone")
@mock.patch("src.materials.material_system._material_for_asset_zone")
def test_checkerboard_uses_spot_keys_when_not_in_image_mode(
    mock_asset: mock.MagicMock,
    mock_checker: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    checker_mat = _create_mock_material("checker_mat")
    mock_checker.return_value = checker_mat
    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "checkerboard",
            "feat_body_texture_spot_color_mode": "single",
            "feat_body_texture_spot_color": "aa11aa",
            "feat_body_texture_spot_bg_color": "11aa11",
            "feat_body_texture_spot_density": 3.0,
        },
    )
    assert out["body"] is checker_mat
    mock_asset.assert_not_called()
    assert mock_checker.call_args.kwargs["color_a_hex"] == "aa11aa"
    assert mock_checker.call_args.kwargs["color_b_hex"] == "11aa11"


@mock.patch("src.materials.material_stripes_zone.material_for_stripes_zone")
@mock.patch("src.materials.material_system._material_for_asset_zone")
def test_stripes_uses_stripe_keys_when_not_in_image_mode(
    mock_asset: mock.MagicMock,
    mock_stripes: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    stripe_mat = _create_mock_material("stripe_mat")
    mock_stripes.return_value = stripe_mat
    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "stripes",
            "feat_body_texture_stripe_color_mode": "single",
            "feat_body_texture_stripe_color": "123456",
            "feat_body_texture_stripe_bg_color": "abcdef",
            "feat_body_texture_stripe_width": 0.33,
        },
    )
    assert out["body"] is stripe_mat
    mock_asset.assert_not_called()
    assert mock_stripes.call_args.kwargs["stripe_hex"] == "123456"
    assert mock_stripes.call_args.kwargs["bg_hex"] == "abcdef"


@mock.patch("src.materials.material_system.material_for_spots_zone")
def test_spots_gradient_mode_blends_a_b_keys(
    mock_spots: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    spots_mat = _create_mock_material("spots_mat")
    mock_spots.return_value = spots_mat
    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_color_mode": "gradient",
            "feat_body_texture_spot_color_a": "ff0000",
            "feat_body_texture_spot_color_b": "0000ff",
            "feat_body_texture_spot_bg_color_mode": "gradient",
            "feat_body_texture_spot_bg_color_a": "00ff00",
            "feat_body_texture_spot_bg_color_b": "000000",
            "feat_body_texture_spot_density": 1.0,
        },
    )
    assert out["body"] is spots_mat
    assert mock_spots.call_args.kwargs["spot_hex"] == "7f007f"
    assert mock_spots.call_args.kwargs["bg_hex"] == "007f00"


@mock.patch("src.materials.material_system.material_for_spots_zone")
@mock.patch("src.materials.material_system._material_for_asset_zone")
def test_spots_image_mode_uses_asset_instead_of_generator(
    mock_asset: mock.MagicMock,
    mock_spots: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    asset_mat = _create_mock_material("asset_mat")
    mock_asset.return_value = asset_mat

    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_color_mode": "image",
            "feat_body_texture_spot_color_image_id": "demo_textures3",
            "feat_body_texture_spot_bg_color_mode": "single",
            "feat_body_texture_spot_bg_color_hex": "00ff00",
            "feat_body_texture_spot_density": 1.0,
        },
    )
    assert out["body"] is asset_mat
    assert mock_asset.call_args.kwargs["asset_id"] == "demo_textures3"
    mock_spots.assert_not_called()


@mock.patch("src.materials.material_system.material_for_spots_zone")
@mock.patch("src.materials.material_system._material_for_asset_zone")
@mock.patch("src.materials.material_types.infer_texture_asset_id_from_preview")
def test_spots_image_mode_uses_preview_to_infer_asset_id(
    mock_infer: mock.MagicMock,
    mock_asset: mock.MagicMock,
    mock_spots: mock.MagicMock,
) -> None:
    base = _create_mock_material("pattern_base")
    asset_mat = _create_mock_material("asset_mat")
    mock_asset.return_value = asset_mat
    mock_infer.return_value = "demo_textures3"

    out = apply_zone_texture_pattern_overrides(
        {"body": base},
        {
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_color_mode": "image",
            "feat_body_texture_spot_color_image_preview": "/api/assets/textures/file/demo%20textures3.png",
            "feat_body_texture_spot_bg_color_mode": "single",
            "feat_body_texture_spot_bg_color_hex": "000000",
            "feat_body_texture_spot_density": 1.0,
        },
    )
    assert out["body"] is asset_mat
    mock_infer.assert_called_once()
    assert mock_asset.call_args.kwargs["asset_id"] == "demo_textures3"
    mock_spots.assert_not_called()
