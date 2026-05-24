"""Tests for zone + per-part feature materials (no Blender scene required)."""

from __future__ import annotations

import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.enemies import animated_imp as imp_mod
from src.enemies.base_animated_model import BaseAnimatedModel
from src.materials import feature_zones as fz
from src.materials import material_system as ms
from src.materials import material_system_enemy_themes as ms_enemy_themes
from src.utils.materials import MaterialNames


class _StubAnimatedModel(BaseAnimatedModel):
    def build_mesh_parts(self) -> None:
        pass


def _fake_mat_with_bsdf_for_uv_gradient() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Minimal node_tree stand-in so ``_add_uv_gradient_to_principled`` runs without bpy."""
    bc_in = MagicMock()
    bc_in.links = [MagicMock()]
    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bsdf.inputs = {"Base Color": bc_in}

    class _FakeNodes:
        def __init__(self) -> None:
            self.created_types: list[str] = []

        def __iter__(self):
            return iter([bsdf])

        def new(self, *, type: str):
            self.created_types.append(type)
            n = MagicMock()
            n.type = type
            if type == "ShaderNodeUVMap":
                n.outputs = {"UV": MagicMock()}
            elif type == "ShaderNodeTexCoord":
                n.outputs = {"UV": MagicMock()}
            elif type == "ShaderNodeTexImage":
                n.inputs = {"Vector": MagicMock()}
                n.outputs = {"Color": MagicMock()}
            elif type == "ShaderNodeMixRGB":
                n.inputs = {
                    "Fac": MagicMock(),
                    "Color1": MagicMock(),
                    "Color2": MagicMock(),
                }
                n.outputs = {"Color": MagicMock()}
            elif type == "ShaderNodeSeparateXYZ":
                n.outputs = {"X": MagicMock(), "Y": MagicMock(), "Z": MagicMock()}
            elif type == "ShaderNodeMix":
                n.inputs = {
                    "Factor": MagicMock(),
                    "A": MagicMock(),
                    "B": MagicMock(),
                }
                n.outputs = {"Result": MagicMock()}
            elif type == "ShaderNodeMath":
                n.inputs = [MagicMock(), MagicMock()]
                n.outputs = {"Value": MagicMock()}
            elif type == "ShaderNodeCombineXYZ":
                n.inputs = {"X": MagicMock(), "Y": MagicMock(), "Z": MagicMock()}
                n.outputs = {"Vector": MagicMock()}
            elif type == "ShaderNodeVectorMath":
                n.inputs = {"Vector": MagicMock()}
                n.outputs = {"Value": MagicMock()}
            return n

    class _FakeLinks:
        def __init__(self) -> None:
            self.removed: list = []
            self.new_calls: list = []

        def remove(self, lk):
            self.removed.append(lk)

        def new(self, *args):
            self.new_calls.append(args)

    fnodes = _FakeNodes()
    flinks = _FakeLinks()
    nt = MagicMock()
    nt.nodes = fnodes
    nt.links = flinks
    mat = MagicMock()
    mat.node_tree = nt
    return mat, flinks, bsdf


def _assert_overlay_zone_material_multiplies_existing_color_graph() -> None:
    mat, links, bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    base_color_socket = bsdf.inputs["Base Color"]
    existing_src = MagicMock()
    base_color_socket.links[0].from_socket = existing_src
    with (
        patch("src.utils.texture_asset_loader.get_texture_asset_filepath", return_value="/tmp/demo.png"),
        patch.object(ms.bpy.data.images, "load", return_value=MagicMock()) as load_img,
    ):
        out = ms.overlay_base_image_on_zone_material(mat, asset_id="demo_textures3")
    assert out is mat
    assert load_img.called
    assert links.new_calls


def _assert_overlay_zone_material_combines_when_pattern_tex_image_exists() -> None:
    mat, _links, bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    base_color_socket = bsdf.inputs["Base Color"]
    pattern_img = MagicMock()
    pattern_img.name = "BlobertTexSpot_body_tex_spot"
    existing_src = MagicMock()
    existing_src.node = MagicMock()
    existing_src.node.image = pattern_img
    base_color_socket.links[0].from_socket = existing_src
    combined_img = MagicMock()
    with (
        patch("src.utils.texture_asset_loader.get_texture_asset_filepath", return_value="/tmp/demo.png"),
        patch.object(ms.bpy.data.images, "load", return_value=MagicMock()) as load_img,
        patch("src.materials.spot_overlay.combine_pattern_over_base_image", return_value=combined_img) as combine,
    ):
        out = ms.overlay_base_image_on_zone_material(mat, asset_id="demo_textures3")
    assert out is mat
    assert load_img.called
    combine.assert_called_once()


def test_add_uv_gradient_to_principled_horizontal() -> None:
    mat, links, _bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    ms._add_uv_gradient_to_principled(
        mat, (1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0, 1.0), "horizontal"
    )
    assert len(links.removed) == 1
    assert links.new_calls


def test_add_uv_gradient_to_principled_vertical() -> None:
    mat, links, _ = _fake_mat_with_bsdf_for_uv_gradient()
    ms._add_uv_gradient_to_principled(
        mat, (1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0, 1.0), "vertical"
    )
    assert links.new_calls


def test_add_uv_gradient_to_principled_radial() -> None:
    mat, links, _ = _fake_mat_with_bsdf_for_uv_gradient()
    ms._add_uv_gradient_to_principled(
        mat, (1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0, 1.0), "radial"
    )
    assert links.new_calls


def test_overlay_base_image_on_material_multiplies_existing_color_graph() -> None:
    _assert_overlay_zone_material_multiplies_existing_color_graph()


def test_overlay_base_image_on_material_reconnects_when_load_fails() -> None:
    mat, links, bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    base_color_socket = bsdf.inputs["Base Color"]
    existing_src = MagicMock()
    base_color_socket.links[0].from_socket = existing_src
    with (
        patch("src.utils.texture_asset_loader.get_texture_asset_filepath", return_value="/tmp/missing.png"),
        patch.object(ms.bpy.data.images, "load", side_effect=IOError("missing")),
    ):
        out = ms.overlay_base_image_on_zone_material(mat, asset_id="missing_id")
    assert out is mat
    assert (existing_src, base_color_socket) in links.new_calls


def test_overlay_base_image_on_material_uses_combined_png_when_pattern_image_exists() -> None:
    _assert_overlay_zone_material_combines_when_pattern_tex_image_exists()


def test_feature_zones_overlay_base_image_handles_unlinked_base_color() -> None:
    mat, links, bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    bsdf.inputs["Base Color"].links = []
    with (
        patch("src.utils.texture_asset_loader.get_texture_asset_filepath", return_value="/tmp/demo.png"),
        patch.object(ms.bpy.data.images, "load", return_value=MagicMock()) as load_img,
    ):
        out = ms.overlay_base_image_on_zone_material(mat, asset_id="demo_textures3")
    assert out is mat
    assert load_img.called
    assert links.new_calls


def test_feature_zones_overlay_base_image_uses_combined_png_when_pattern_image_exists() -> None:
    _assert_overlay_zone_material_combines_when_pattern_tex_image_exists()


def test_apply_zone_texture_pattern_overrides_blends_zone_image_with_pattern() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    patterned = MagicMock(name="patterned")
    with (
        patch.object(ms, "_apply_spots_pattern", return_value=patterned) as apply_spots,
    ):
        out = ms.apply_zone_texture_pattern_overrides(
            {"body": base},
            {
                "feat_body_texture_mode": "spots",
                "features": {
                    "body": {
                        "color_image": {"mode": "image", "id": "demo_textures3"},
                    }
                },
            },
        )
    assert out["body"] is patterned
    apply_spots.assert_called_once()
    assert apply_spots.call_args.kwargs["zone"] == "body"
    assert apply_spots.call_args.kwargs["build_options"]["features"]["body"]["color_image"]["id"] == "demo_textures3"


def test_zone_color_image_asset_id_prefers_id_and_preview() -> None:
    """_zone_color_image_asset_id is now only in material_system (removed duplicate from feature_zones)."""
    zone = ms.FeatureZoneOptions.from_mapping({"color_image": {"mode": "image", "id": "demo_textures3"}})
    assert ms._zone_color_image_asset_id(zone) == "demo_textures3"
    zone_preview = ms.FeatureZoneOptions.from_mapping(
        {"color_image": {"mode": "image", "preview": "/api/assets/textures/file/demo%20textures3.png"}}
    )
    assert ms._zone_color_image_asset_id(zone_preview) == "demo_textures3"


def test_overlay_base_image_returns_early_for_empty_asset() -> None:
    mat = MagicMock()
    assert ms.overlay_base_image_on_zone_material(mat, asset_id="", base_path=None) is mat


def test_overlay_mask_combine_crops_underlay_spot_plate_already_rect_sized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Underlay is cropped to atlas rect; spot plate is generated at that size — combine without pattern crop."""
    mat, _links, bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    base_color_socket = bsdf.inputs["Base Color"]
    pattern_img = MagicMock()
    pattern_img.name = "BlobertTexSpot_body_tex_spot"
    existing_src = MagicMock()
    existing_src.node = MagicMock()
    existing_src.node.image = pattern_img
    base_color_socket.links[0].from_socket = existing_src
    fake_pat = tmp_path / "full_atlas.png"
    fake_pat.write_bytes(b"x")

    cropped_for_combine = Path("/cropped_for_combine.png")
    monkeypatch.setattr(
        "src.materials.spot_overlay.resolved_asset_path_for_image_sampling",
        lambda p, uv: cropped_for_combine if uv else Path(p),
    )
    combined = MagicMock()
    with (
        patch("src.materials.spot_overlay._resolve_pattern_sources", return_value=(fake_pat, None)),
        patch("src.materials.spot_overlay.combine_pattern_over_base_image", return_value=combined) as combine_fn,
        patch("src.materials.spot_overlay._wire_tex_uv_to_base_color") as wire_fn,
        patch.object(ms.bpy.data.images, "load", return_value=MagicMock()),
        patch("src.utils.texture_asset_loader.get_texture_asset_filepath", return_value="/tmp/demo.png"),
    ):
        ms.overlay_base_image_on_zone_material(
            mat,
            asset_id="demo_textures3",
            underlay_uv_rect=(0.2, 0.3, 0.8, 0.9),
        )
    combine_fn.assert_called_once()
    assert combine_fn.call_args[0][0] == fake_pat
    assert combine_fn.call_args[0][1] == cropped_for_combine
    wire_fn.assert_called_once()
    assert wire_fn.call_args.kwargs.get("uv_rect") is None


def test_overlay_base_image_prefers_tagged_spot_image() -> None:
    mat, _links, bsdf = _fake_mat_with_bsdf_for_uv_gradient()

    def _contains_fn(_self: object, *args: object) -> bool:
        key = args[0] if args else None
        return key == "blobert_spot_image_name"

    mat.__contains__ = types.MethodType(_contains_fn, mat)  # type: ignore[method-assign]

    def _mat_getitem(self: object, key: object) -> str:
        if key == "blobert_spot_image_name":
            return "BlobertTexSpot_body_tex_spot"
        raise KeyError(key)

    mat.__getitem__ = types.MethodType(_mat_getitem, mat)  # type: ignore[method-assign]
    existing_src = MagicMock()
    existing_src.node = MagicMock()
    existing_src.node.image = MagicMock(name="non_pattern_image")
    bsdf.inputs["Base Color"].links[0].from_socket = existing_src
    tagged_img = MagicMock(name="tagged_spot")
    tagged_img.filepath_raw = ""
    tagged_img.file_format = "PNG"
    tagged_img.save = MagicMock()
    with (
        patch.object(ms.bpy.data.images, "get", return_value=tagged_img),
        patch("src.materials.spot_overlay.combine_pattern_over_base_image", return_value=MagicMock()) as combine,
        patch("src.utils.texture_asset_loader.get_texture_asset_filepath", return_value="/tmp/demo.png"),
        patch.object(ms.bpy.data.images, "load", return_value=MagicMock()),
    ):
        ms.overlay_base_image_on_zone_material(mat, asset_id="demo_textures3")
    assert combine.called
    assert combine.call_args.args[0] is not None


def test_overlay_base_image_enables_nodes_and_returns_when_node_tree_missing() -> None:
    mat = MagicMock()
    mat.use_nodes = False
    mat.node_tree = None
    out = ms.overlay_base_image_on_zone_material(mat, asset_id="demo_textures3")
    assert out is mat
    assert mat.use_nodes is True


def test_overlay_base_image_returns_when_bsdf_or_base_socket_missing() -> None:
    mat, _links, _bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    with patch.object(ms, "_find_principled_bsdf", return_value=None):
        assert ms.overlay_base_image_on_zone_material(mat, asset_id="demo_textures3") is mat
    with (
        patch.object(ms, "_find_principled_bsdf", return_value=MagicMock()),
        patch.object(ms, "_principled_base_color_socket", return_value=None),
    ):
        assert ms.overlay_base_image_on_zone_material(mat, asset_id="demo_textures3") is mat


def test_feature_zones_overlay_base_image_multiplies_existing_color_graph() -> None:
    _assert_overlay_zone_material_multiplies_existing_color_graph()


def test_feature_zones_apply_zone_texture_pattern_overrides_blends_zone_image() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    patterned = MagicMock(name="patterned")
    with (
        patch.object(fz, "_material_for_gradient_zone", return_value=patterned),
        patch.object(fz, "overlay_base_image_on_zone_material", return_value=patterned) as blend,
    ):
        out = fz.apply_zone_texture_pattern_overrides(
            {"body": base},
            {
                "feat_body_texture_mode": "gradient",
                "features": {
                    "body": {
                        "color_image": {"mode": "image", "id": "demo_textures3"},
                    }
                },
            },
        )
    assert out["body"] is patterned
    blend.assert_called_once()


def test_spots_pattern_no_overlay_even_when_zone_image_present() -> None:
    """Spots pipeline returns directly — no overlay_base_image_on_zone_material call.

    When ``feat_body_texture_pattern_mode`` is "image" but no ``image_id`` is
    provided, the FillMaterial dispatcher creates an ``ImageFill(asset_id="")``
    which falls through to the procedural spot path (empty asset_id).
    The zone color_image is NOT composited on top for spots mode.
    """
    base = MagicMock()
    base.name = "Organic_Brown"
    spots = MagicMock(name="spots")
    with (
        patch.object(ms, "material_for_spots_zone", return_value=spots) as mk,
        patch.object(ms, "overlay_base_image_on_zone_material") as blend,
    ):
        out = ms.apply_zone_texture_pattern_overrides(
            {"body": base},
            {
                "feat_body_texture_mode": "spots",
                "feat_body_texture_pattern_mode": "image",
                "features": {"body": {"color_image": {"mode": "image", "id": "demo_textures3"}}},
            },
        )
    assert out["body"] is spots
    mk.assert_called_once()
    # New API: pattern_fill and background_fill are FillMaterial objects
    assert "pattern_fill" in mk.call_args.kwargs
    assert "background_fill" in mk.call_args.kwargs
    # Spots mode does NOT overlay zone image (simplified pipeline)
    blend.assert_not_called()


def test_material_for_gradient_zone_is_diffuse_for_export_even_on_metal_palette() -> (
    None
):
    new_mat = MagicMock()
    with (
        patch.object(ms, "create_material", return_value=new_mat) as cm,
        patch.object(ms, "_add_uv_gradient_to_principled") as grad,
    ):
        got = ms._material_for_gradient_zone(
            base_palette_name="Metal_Silver",
            finish="matte",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="",
            instance_suffix="body_tex_grad",
        )
    assert got is new_mat
    assert cm.called
    assert cm.call_args[0][2] == 0.0
    assert grad.called
    assert grad.call_args.kwargs.get("image_label") == "body_tex_grad"


def test_themed_slot_materials_chains_zone_texture_pattern_overrides() -> None:
    rng = MagicMock()
    base_m = MagicMock()
    base_m.name = "Organic_Brown"
    palette = {"Organic_Brown": base_m}
    fake_slots = {
        "body": base_m,
        "head": base_m,
        "limbs": base_m,
        "joints": base_m,
        "extra": base_m,
    }
    grad_mat = MagicMock(name="grad_body")
    with (
        patch(
            "src.enemies.base_animated_model.get_enemy_materials",
            return_value=fake_slots,
        ),
        patch.object(ms, "create_material", return_value=grad_mat),
        patch.object(ms, "_add_uv_gradient_to_principled"),
    ):
        model = _StubAnimatedModel(
            "spider",
            palette,
            rng,
            build_options={
                "feat_body_texture_mode": "gradient",
                "feat_body_texture_grad_color_a": "ff0000",
                "feat_body_texture_grad_color_b": "0000ff",
            },
        )
        out = model._themed_slot_materials_for("spider")
    assert out["body"] is grad_mat


def test_palette_base_name_strips_data_name_and_feat_suffix() -> None:
    m = MagicMock()
    m.name = "Organic_Brown__feat_limbs.002"
    assert ms._palette_base_name_from_material(m) == "Organic_Brown"


def test_apply_feature_slot_overrides_updates_joints_slot() -> None:
    base = MagicMock()
    base.name = "Bone_White"
    slots = {"body": base, "head": base, "limbs": base, "joints": base, "extra": base}
    new_mat = MagicMock(name="new_joint_mat")
    with patch.object(ms, "create_material", return_value=new_mat) as cm:
        out = ms.apply_feature_slot_overrides(
            slots, {"joints": {"hex": "00aa11", "finish": "matte"}}
        )
    assert out["joints"] is new_mat
    assert cm.called


@patch.object(ms, "material_for_color_image_zone")
def test_apply_feature_slot_overrides_nested_color_image_delegates_to_image_helper(
    mock_color_img: MagicMock,
) -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    new_mat = MagicMock(name="from_image")
    mock_color_img.return_value = new_mat
    slots = {"body": base}
    out = ms.apply_feature_slot_overrides(
        slots,
        {
            "body": {
                "color_image": {"mode": "image", "id": "demo_textures3"},
            }
        },
    )
    assert out["body"] is new_mat
    mock_color_img.assert_called_once()
    assert mock_color_img.call_args.kwargs["asset_id"] == "demo_textures3"


@patch.object(ms, "material_for_color_image_zone")
def test_apply_feature_slot_overrides_color_image_infers_asset_id_from_preview(
    mock_color_img: MagicMock,
) -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    new_mat = MagicMock(name="from_preview")
    mock_color_img.return_value = new_mat
    slots = {"body": base}
    out = ms.apply_feature_slot_overrides(
        slots,
        {
            "body": {
                "color_image": {
                    "mode": "image",
                    "preview": "/api/assets/textures/file/demo%20textures3.png",
                },
            },
        },
    )
    assert out["body"] is new_mat
    mock_color_img.assert_called_once()
    assert mock_color_img.call_args.kwargs["asset_id"] == "demo_textures3"


def test_apply_zone_texture_gradient_replaces_slot_and_calls_gradient_setup() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base, "head": base}
    new_mat = MagicMock(name="grad_mat")
    with (
        patch.object(ms, "create_material", return_value=new_mat) as cm,
        patch.object(ms, "_add_uv_gradient_to_principled") as grad,
    ):
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {
                "feat_body_texture_mode": "gradient",
                "feat_body_texture_grad_color_a": "ff0000",
                "feat_body_texture_grad_color_b": "0000ff",
                "feat_body_texture_grad_direction": "horizontal",
            },
        )
    assert out["body"] is new_mat
    assert out["head"] is base
    assert cm.called
    assert grad.called


def test_apply_zone_texture_gradient_uses_zone_hex_when_grad_hexes_empty() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base}
    new_mat = MagicMock(name="grad_mat")
    with (
        patch.object(ms, "create_material", return_value=new_mat) as cm,
        patch.object(ms, "_add_uv_gradient_to_principled"),
    ):
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {
                "feat_body_texture_mode": "gradient",
                "features": {"body": {"finish": "default", "hex": "aabbcc"}},
            },
        )
    assert out["body"] is new_mat
    assert cm.called


def test_apply_zone_texture_gradient_applies_with_fallback_when_no_hex() -> None:
    """Gradients always apply when mode=gradient; empty hex uses fallback logic."""
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base}
    with patch.object(ms, "create_material") as cm:
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {
                "feat_body_texture_mode": "gradient",
                "features": {"body": {"finish": "default", "hex": ""}},
            },
        )
    assert out["body"] is not base
    assert cm.called


def test_apply_zone_texture_checkerboard_overlays_image_when_spot_color_image_mode() -> None:
    # When spot_color is in image mode, it's used to compute the checker colors (via resolved_hex),
    # not as an overlay. Only spot_bg_color in image mode causes overlaying.
    base = MagicMock()
    base.name = "Organic_Brown"
    checker_mat = MagicMock(name="checker_mat")
    with patch.object(ms, "_material_for_checkerboard_zone", return_value=checker_mat):
        with patch.object(ms, "overlay_base_image_on_zone_material") as ov:
            out = ms.apply_zone_texture_pattern_overrides(
                {"body": base},
                {
                    "feat_body_texture_mode": "checkerboard",
                    "feat_body_texture_pattern_mode": "image",
                    "feat_body_texture_pattern_image_id": "demo_textures3",
                    "feat_body_texture_asset_tile_repeat": 1.25,
                },
            )
    # No overlay should happen when only spot_color is in image mode
    assert out["body"] is checker_mat
    ov.assert_not_called()


def test_apply_zone_texture_stripes_overlays_image_when_stripe_color_image_mode() -> None:
    # When stripe_color is in image mode, it's used to compute stripe colors (via resolved_hex),
    # not as an overlay. Only stripe_bg_color in image mode causes overlaying.
    base = MagicMock()
    base.name = "Organic_Brown"
    stripe_mat = MagicMock(name="stripe_mat")
    with (
        patch("src.materials.material_stripes_zone.material_for_stripes_zone", return_value=stripe_mat) as msz,
        patch.object(ms, "overlay_base_image_on_zone_material") as ov,
    ):
        out = ms.apply_zone_texture_pattern_overrides(
            {"body": base},
            {
                "feat_body_texture_mode": "stripes",
                "feat_body_texture_pattern_mode": "image",
                "feat_body_texture_pattern_image_id": "demo_textures3",
                "feat_body_texture_asset_tile_repeat": 1.5,
            },
        )
    # No overlay should happen when only stripe_color is in image mode
    assert out["body"] is stripe_mat
    msz.assert_called_once()
    ov.assert_not_called()


def test_apply_zone_texture_stripes_uses_zone_color_uv_when_overlay_reuses_zone_body_asset() -> None:
    """Zone color image overlay happens once in outer loop when stripe pattern has no explicit image."""
    base = MagicMock()
    base.name = "Organic_Brown"
    stripe_mat = MagicMock(name="stripe_mat")
    overlaid = MagicMock(name="stripe_overlay")
    rect = '{"u0":0,"v0":0,"u1":0.25,"v1":0.25}'
    with (
        patch("src.materials.material_stripes_zone.material_for_stripes_zone", return_value=stripe_mat),
        patch.object(ms, "overlay_base_image_on_zone_material", return_value=overlaid) as ov,
    ):
        ms.apply_zone_texture_pattern_overrides(
            {"body": base},
            {
                "feat_body_texture_mode": "stripes",
                "feat_body_texture_pattern_mode": "single",
                "feat_body_texture_pattern_hex": "ff0000",
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "shared_atlas",
                "feat_body_color_image_uv_rect": rect,
            },
        )
    assert ov.call_count == 1
    expected = (0.0, 0.0, 0.25, 0.25)
    assert ov.call_args_list[0].kwargs["asset_id"] == "shared_atlas"
    assert ov.call_args_list[0].kwargs["underlay_uv_rect"] == expected


def test_apply_zone_texture_checkerboard_uses_zone_color_uv_when_overlay_reuses_zone_body_asset() -> None:
    """Zone color image overlay happens once in outer loop when checkerboard pattern has no explicit image."""
    base = MagicMock()
    base.name = "Organic_Brown"
    checker_mat = MagicMock(name="checker_mat")
    overlaid = MagicMock(name="checker_overlay")
    rect = '{"u0":0.1,"v0":0.2,"u1":0.3,"v1":0.4}'
    with (
        patch.object(ms, "_material_for_checkerboard_zone", return_value=checker_mat),
        patch.object(ms, "overlay_base_image_on_zone_material", return_value=overlaid) as ov,
    ):
        ms.apply_zone_texture_pattern_overrides(
            {"body": base},
            {
                "feat_body_texture_mode": "checkerboard",
                "feat_body_texture_pattern_mode": "single",
                "feat_body_texture_pattern_hex": "00ff00",
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "shared_atlas",
                "feat_body_color_image_uv_rect": rect,
            },
        )
    assert ov.call_count == 1
    expected = (0.1, 0.2, 0.3, 0.4)
    assert ov.call_args_list[0].kwargs["asset_id"] == "shared_atlas"
    assert ov.call_args_list[0].kwargs["underlay_uv_rect"] == expected


def test_rgba_from_hex_or_fallback_returns_fallback_when_parse_raises() -> None:
    with (
        patch.object(ms, "_sanitize_hex_input", return_value="abcdef"),
        patch.object(ms, "parse_hex_color", side_effect=ValueError),
    ):
        fb = (0.1, 0.2, 0.3, 1.0)
        assert ms._rgba_from_hex_or_fallback("ignored", fb) == fb


def test_add_uv_gradient_returns_when_no_node_tree() -> None:
    mat = MagicMock()
    mat.node_tree = None
    ms._add_uv_gradient_to_principled(mat, (1, 0, 0, 1), (0, 0, 1, 1), "horizontal")


def test_add_uv_gradient_returns_when_no_bsdf() -> None:
    class _EmptyNodes:
        def __iter__(self):
            return iter([])

    nt = MagicMock()
    nt.nodes = _EmptyNodes()
    mat = MagicMock()
    mat.node_tree = nt
    ms._add_uv_gradient_to_principled(mat, (1, 0, 0, 1), (0, 0, 1, 1), "horizontal")


def test_add_uv_gradient_returns_when_no_base_color_socket() -> None:
    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bsdf.inputs = {}

    class _OneNode:
        def __iter__(self):
            return iter([bsdf])

    nt = MagicMock()
    nt.nodes = _OneNode()
    mat = MagicMock()
    mat.node_tree = nt
    ms._add_uv_gradient_to_principled(mat, (1, 0, 0, 1), (0, 0, 1, 1), "horizontal")


def test_apply_zone_texture_pattern_overrides_empty_build_options() -> None:
    base = MagicMock()
    slots = {"body": base}
    assert ms.apply_zone_texture_pattern_overrides(slots, {}) is slots
    assert ms.apply_zone_texture_pattern_overrides(slots, None) is slots


def test_apply_zone_texture_none_leaves_slots() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base}
    with patch.object(ms, "create_material") as cm:
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {"feat_body_texture_mode": "none"},
        )
    assert out["body"] is base
    assert not cm.called


def test_material_for_zone_part_creates_variant_when_part_hex_set() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb, "joints": limb}
    features = {
        "limbs": {
            "finish": "default",
            "hex": "",
            "parts": {"arm_0": {"finish": "default", "hex": "cc00dd"}},
        }
    }
    new_mat = MagicMock()
    with patch.object(ms, "create_material", return_value=new_mat) as cm:
        got = fz.material_for_zone_part("limbs", "arm_0", slots, features)
    assert got is new_mat
    assert cm.called


def test_material_for_zone_part_returns_base_when_no_override() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert fz.material_for_zone_part("limbs", "arm_0", slots, {"limbs": {}}) is limb


def test_material_for_zone_part_returns_none_when_zone_slot_missing() -> None:
    assert fz.material_for_zone_part("limbs", "arm_0", {}, {"limbs": {}}) is None


def test_material_for_zone_part_returns_base_when_zone_feature_not_dict() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert fz.material_for_zone_part("limbs", "arm_0", slots, {"limbs": "nope"}) is limb


def test_material_for_zone_part_inherits_zone_hex_when_part_sets_finish_only() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    features = {
        "limbs": {
            "finish": "default",
            "hex": "aabbcc",
            "parts": {"arm_0": {"finish": "glossy", "hex": ""}},
        }
    }
    new_mat = MagicMock()
    with patch.object(ms, "create_material", return_value=new_mat):
        got = fz.material_for_zone_part("limbs", "arm_0", slots, features)
    assert got is new_mat


def test_material_for_zone_part_ignores_non_dict_parts_map() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert (
        fz.material_for_zone_part(
            "limbs",
            "arm_0",
            slots,
            {"limbs": {"parts": "bad"}},
        )
        is limb
    )


def test_material_for_zone_part_ignores_non_dict_part_payload() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert (
        fz.material_for_zone_part(
            "limbs",
            "arm_0",
            slots,
            {"limbs": {"parts": {"arm_0": "nope"}}},
        )
        is limb
    )


def test_material_for_zone_geometry_extra_returns_base_when_no_override() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"body": limb}
    assert (
        fz.material_for_zone_geometry_extra("body", slots, {"body": {}}, "default", "")
        is limb
    )


def test_material_for_zone_geometry_extra_creates_when_extra_hex() -> None:
    b = MagicMock()
    b.name = "Organic_Brown"
    slots = {"body": b}
    new_m = MagicMock()
    with patch.object(ms, "create_material", return_value=new_m) as cm:
        got = fz.material_for_zone_geometry_extra(
            "body", slots, None, "default", "ff00aa"
        )
    assert got is new_m
    assert cm.called


def test_material_for_zone_geometry_extra_uses_zone_hex_when_extra_empty() -> None:
    """Reads zone feature hex/finish when geometry extra does not supply hex."""
    b = MagicMock()
    b.name = "Organic_Brown"
    slots = {"body": b}
    new_m = MagicMock()
    features = {"body": {"finish": "default", "hex": "00aa11"}}
    with patch.object(ms, "create_material", return_value=new_m) as cm:
        got = fz.material_for_zone_geometry_extra("body", slots, features, "default", "")
    assert got is new_m
    assert cm.called


def test_material_for_zone_geometry_extra_returns_none_when_slot_missing() -> None:
    assert (
        fz.material_for_zone_geometry_extra("body", {}, {}, "matte", "aabbcc") is None
    )


def test_get_enemy_materials_single_theme_color_fills_all_slots() -> None:
    m0 = MagicMock(name="M0")
    palette = {"M0": m0}
    rng = MagicMock()
    with (
        patch.object(ms_enemy_themes.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms_enemy_themes.MaterialThemes, "get_theme", return_value=("M0",)),
    ):
        out = ms.get_enemy_materials("solo_theme", palette, rng)
    assert out["joints"] is m0
    assert out["limbs"] is m0


def test_get_enemy_materials_joint_slot_matches_limbs_for_three_theme_colors() -> None:
    palette = {f"M{i}": MagicMock(name=f"M{i}") for i in range(3)}
    rng = MagicMock()
    rng.choice = MagicMock(side_effect=lambda seq: seq[-1])
    with (
        patch.object(ms_enemy_themes.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms_enemy_themes.MaterialThemes, "get_theme", return_value=("M0", "M1", "M2")),
    ):
        out = ms.get_enemy_materials("test_enemy", palette, rng)
    assert out["limbs"] is palette["M2"]
    assert out["joints"] is palette["M2"]


def test_get_enemy_materials_unknown_enemy_uses_default_palette_slots() -> None:
    """Enemy names with no registered theme map body/head/limbs/joints/extra from defaults."""
    brown = MagicMock()
    pink = MagicMock()
    bone = MagicMock()
    palette = {
        MaterialNames.ORGANIC_BROWN: brown,
        MaterialNames.FLESH_PINK: pink,
        MaterialNames.BONE_WHITE: bone,
    }
    rng = MagicMock()
    out = ms_enemy_themes.get_enemy_materials(
        "enemy_with_no_theme_registry_entry_901", palette, rng
    )
    assert out["body"] is brown
    assert out["head"] is pink
    assert out["limbs"] is bone
    assert out["joints"] is bone
    assert out["extra"] is brown


def test_get_enemy_materials_two_theme_materials_reuses_first_for_limbs_and_joints() -> None:
    ma, mb = MagicMock(name="MA"), MagicMock(name="MB")
    palette = {"MA": ma, "MB": mb}
    rng = MagicMock()
    with (
        patch.object(ms_enemy_themes.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms_enemy_themes.MaterialThemes, "get_theme", return_value=("MA", "MB")),
    ):
        out = ms_enemy_themes.get_enemy_materials("two_slot_theme", palette, rng)
    assert out["body"] is ma
    assert out["head"] is mb
    assert out["limbs"] is ma
    assert out["joints"] is ma
    assert out["extra"] is mb


@pytest.mark.parametrize(
    ("n_seg", "joint_vis", "end_shape", "expected_len"),
    [
        (1, False, "none", 1),
        (2, True, "sphere", 4),
        (1, True, "sphere", 2),
    ],
)
def test_humanoid_limb_part_kinds_length(
    n_seg: int,
    joint_vis: bool,
    end_shape: str,
    expected_len: int,
) -> None:
    seq = imp_mod._humanoid_limb_part_kinds(n_seg, joint_vis, end_shape)
    assert len(seq) == expected_len
