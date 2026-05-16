"""Targeted coverage for material_system helpers in the diff vs origin/main."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.materials.material_system import (
    fill_material_hex,
    fill_material_image_asset_id,
    resolve_spots_composite_underlay,
    resolve_texture_pattern_overlay_uv_rect,
    resolve_zone_color_image_asset_id,
    resolve_zone_color_image_uv_rect,
)
from src.materials.material_types import (
    ColorImageOptions,
    FeatureZoneOptions,
    GradientFill,
    ImageFill,
    SolidFill,
    ZoneTextureOptions,
)
from src.materials.spot_plate_mask import DEFAULT_DARK_THRESHOLD


def test_fill_material_hex_and_image_asset_dispatch() -> None:
    assert fill_material_hex(SolidFill(hex_value="aabbcc")) == "aabbcc"
    assert fill_material_hex(GradientFill(hex_a="ff0000", hex_b="00ff00", direction="h")) == "ff0000"
    assert fill_material_hex(ImageFill(asset_id="x", uv_rect=None), fallback="fb") == "fb"

    assert fill_material_image_asset_id(SolidFill(hex_value="x")) == ""
    assert fill_material_image_asset_id(GradientFill(hex_a="a", hex_b="b", direction="h")) == ""
    assert fill_material_image_asset_id(ImageFill(asset_id="tex1", uv_rect=None)) == "tex1"


def test_resolve_zone_color_image_asset_id_flat_keys_and_preview() -> None:
    zf = FeatureZoneOptions(
        finish="default",
        hex_value="",
        color_image=None,
        parts={},
    )
    assert resolve_zone_color_image_asset_id("body", {}, zf) == ""

    assert (
        resolve_zone_color_image_asset_id(
            "body",
            {"feat_body_color_mode": "image", "feat_body_color_image_id": " atlas1 "},
            zf,
        )
        == "atlas1"
    )

    with patch(
        "src.materials.material_system.infer_texture_asset_id_from_preview",
        return_value="from_preview",
    ):
        assert (
            resolve_zone_color_image_asset_id(
                "body",
                {
                    "feat_body_color_mode": "image",
                    "feat_body_color_image_preview": "  blob://x  ",
                },
                zf,
            )
            == "from_preview"
        )


def test_resolve_zone_color_image_uv_rect_nested_and_flat() -> None:
    zf = FeatureZoneOptions(
        finish="default",
        hex_value="",
        color_image=ColorImageOptions(
            mode="image",
            asset_id="a",
            preview="",
            uv_rect=(0.1, 0.2, 0.3, 0.4),
        ),
        parts={},
    )
    assert resolve_zone_color_image_uv_rect("body", {}, zf) == (0.1, 0.2, 0.3, 0.4)

    zf2 = FeatureZoneOptions(finish="default", hex_value="", color_image=None, parts={})
    rect = '{"u0":0,"v0":0,"u1":0.5,"v1":0.5}'
    assert resolve_zone_color_image_uv_rect("body", {"feat_body_color_image_uv_rect": rect}, zf2) == (
        0.0,
        0.0,
        0.5,
        0.5,
    )


def test_resolve_texture_pattern_overlay_prefers_channel_then_zone_bounds() -> None:
    zf = FeatureZoneOptions(finish="default", hex_value="", color_image=None, parts={})
    uv = (0.0, 0.0, 0.25, 0.25)
    assert (
        resolve_texture_pattern_overlay_uv_rect(
            zone="body",
            build_options={},
            zone_feature=zf,
            pattern_asset_id="shared",
            zone_image_asset_id="shared",
            channel_uv_rect=uv,
        )
        == uv
    )

    rect = '{"u0":0.1,"v0":0.1,"u1":0.9,"v1":0.9}'
    assert (
        resolve_texture_pattern_overlay_uv_rect(
            zone="body",
            build_options={"feat_body_color_image_uv_rect": rect},
            zone_feature=zf,
            pattern_asset_id="shared",
            zone_image_asset_id="shared",
            channel_uv_rect=None,
        )
        == (0.1, 0.1, 0.9, 0.9)
    )

    assert (
        resolve_texture_pattern_overlay_uv_rect(
            zone="body",
            build_options={},
            zone_feature=zf,
            pattern_asset_id="a",
            zone_image_asset_id="b",
            channel_uv_rect=None,
        )
        is None
    )


def test_wire_spot_plate_image_skips_without_node_tree() -> None:
    from src.materials.material_system import _wire_spot_plate_image_to_principled

    mat = MagicMock()
    mat.node_tree = None
    _wire_spot_plate_image_to_principled(
        mat,
        MagicMock(name="img"),
        use_atlas_mapping=False,
        uv_rect=None,
    )


def test_wire_spot_plate_image_links_uv_and_texture_with_mapping() -> None:
    from src.materials.material_system import _wire_spot_plate_image_to_principled

    bc_in = MagicMock()
    bc_in.links = []
    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bsdf.inputs = {"Base Color": bc_in}

    class _FN:
        def __iter__(self):
            return iter([bsdf])

        def new(self, type: str) -> MagicMock:  # noqa: A002
            n = MagicMock()
            n.type = type
            n.inputs = {"Vector": MagicMock(), "Scale": MagicMock(), "Location": MagicMock()}
            n.outputs = {"UV": MagicMock(), "Vector": MagicMock(), "Color": MagicMock()}
            n.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
            n.inputs["Location"].default_value = (0.0, 0.0, 0.0)
            return n

    links = MagicMock()
    nt = MagicMock()
    nt.nodes = _FN()
    nt.links = links
    mat = MagicMock()
    mat.node_tree = nt
    img = MagicMock()

    _wire_spot_plate_image_to_principled(
        mat,
        img,
        use_atlas_mapping=True,
        uv_rect=(0.0, 0.0, 0.5, 0.5),
    )
    assert links.new.called


def test_wire_spot_plate_returns_early_without_bsdf() -> None:
    from src.materials.material_system import _wire_spot_plate_image_to_principled

    class _EmptyNodes:
        def __iter__(self):
            return iter([])

    nt = MagicMock()
    nt.nodes = _EmptyNodes()
    nt.links = MagicMock()
    mat = MagicMock()
    mat.node_tree = nt
    _wire_spot_plate_image_to_principled(mat, MagicMock(), use_atlas_mapping=False, uv_rect=None)


def test_resolve_zone_color_image_asset_id_image_mode_no_underlay_source() -> None:
    zf = FeatureZoneOptions(finish="default", hex_value="", color_image=None, parts={})
    with patch("src.materials.material_system.log_spots_composite") as log:
        assert (
            resolve_zone_color_image_asset_id(
                "body",
                {"feat_body_color_mode": "image"},
                zf,
            )
            == ""
        )
    assert log.called


def test_wire_spot_plate_returns_early_without_base_color_socket() -> None:
    from src.materials.material_system import _wire_spot_plate_image_to_principled

    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    ins = MagicMock()

    def _no_bc(_k: str) -> None:
        return None

    ins.get = _no_bc
    bsdf.inputs = ins

    class _Nodes:
        def __iter__(self):
            return iter([bsdf])

        def new(self, _type: str) -> MagicMock:  # noqa: A002
            return MagicMock()

    nt = MagicMock()
    nt.nodes = _Nodes()
    nt.links = MagicMock()
    mat = MagicMock()
    mat.node_tree = nt
    _wire_spot_plate_image_to_principled(
        mat, MagicMock(), use_atlas_mapping=False, uv_rect=(0.0, 0.0, 1.0, 1.0)
    )


def test_wire_spot_plate_uv_rect_none_skips_mapping_node() -> None:
    from src.materials.material_system import _wire_spot_plate_image_to_principled

    bc_in = MagicMock()
    bc_in.links = []
    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bsdf.inputs = {"Base Color": bc_in}
    new_types: list[str] = []

    class _Nodes:
        def __iter__(self):
            return iter([bsdf])

        def new(self, type: str) -> MagicMock:  # noqa: A002
            new_types.append(type)
            n = MagicMock()
            n.type = type
            n.inputs = {"Vector": MagicMock(), "Scale": MagicMock(), "Location": MagicMock()}
            n.outputs = {"UV": MagicMock(), "Vector": MagicMock(), "Color": MagicMock()}
            return n

    links = MagicMock()
    nt = MagicMock()
    nt.nodes = _Nodes()
    nt.links = links
    mat = MagicMock()
    mat.node_tree = nt
    _wire_spot_plate_image_to_principled(
        mat, MagicMock(name="img"), use_atlas_mapping=False, uv_rect=None
    )
    assert "ShaderNodeMapping" not in new_types
    assert links.new.called


@patch("src.materials.material_system.is_full_uv_rect", return_value=False)
@patch(
    "src.materials.material_system.mapping_scale_location_for_uv_rect",
    return_value=((2.0, 2.0, 1.0), (0.1, 0.2, 0.0)),
)
@patch("src.materials.material_system.bpy.data.images")
@patch("src.materials.material_system.get_texture_asset_filepath")
def test_material_for_color_image_zone_partial_uv_rect_adds_mapping(
    mock_get_path: MagicMock,
    mock_images: MagicMock,
    _mock_scale: MagicMock,
    _mock_full: MagicMock,
) -> None:
    from src.materials.material_system import material_for_color_image_zone

    mock_get_path.return_value = Path("/tmp/color_atlas.png")
    mock_images.load.return_value = MagicMock()

    p = type("ShaderNodeBsdfPrincipled", (), {})()
    p.type = "BSDF_PRINCIPLED"
    p.inputs = {"Base Color": MagicMock()}
    new_types: list[str] = []

    class _Nodes:
        def __iter__(self):
            return iter([p])

        def new(self, type: str) -> MagicMock:  # noqa: A002
            new_types.append(type)
            n = MagicMock()
            n.outputs = {"UV": MagicMock(), "Vector": MagicMock(), "Color": MagicMock()}
            n.inputs = {"Vector": MagicMock(), "Scale": MagicMock(), "Location": MagicMock()}
            n.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
            n.inputs["Location"].default_value = (0.0, 0.0, 0.0)
            return n

    flinks = MagicMock()
    nt = MagicMock()
    nt.nodes = _Nodes()
    nt.links = flinks
    copy_mat = MagicMock()
    copy_mat.name = "ci"
    copy_mat.use_nodes = True
    copy_mat.node_tree = nt
    base = MagicMock()
    base.name = "base"
    base.use_nodes = True
    base.node_tree = nt
    base.copy.return_value = copy_mat

    with patch("src.materials.material_system.bpy.types.ShaderNodeBsdfPrincipled", type(p)):
        out = material_for_color_image_zone(
            base,
            "demo_textures3",
            uv_rect=(0.0, 0.0, 0.5, 0.5),
        )
    assert out is copy_mat
    assert "ShaderNodeMapping" in new_types


def _zone_options(**kwargs: object) -> ZoneTextureOptions:
    defaults: dict[str, object] = {
        "zone": "body",
        "mode": "spots",
        "finish": "default",
        "zone_hex": "",
        "tile_repeat": 1.0,
        "gradient_a_hex": "",
        "gradient_b_hex": "",
        "gradient_direction": "horizontal",
        "asset_id": "",
        "spot_density": 1.0,
        "stripe_width": 0.2,
        "stripe_preset": "beachball",
        "stripe_yaw": 0.0,
        "stripe_pitch": 0.0,
        "pattern_fill": SolidFill(hex_value=""),
        "background_fill": SolidFill(hex_value="eeeeee"),
        "spot_plate_mask_mode": "auto",
        "spot_plate_dark_threshold": DEFAULT_DARK_THRESHOLD,
        "spot_plate_mask_soft_edges": True,
    }
    defaults.update(kwargs)
    return ZoneTextureOptions(**defaults)  # type: ignore[arg-type]


@patch("src.materials.material_system._wire_spot_plate_image_to_principled")
@patch("src.materials.material_system.bpy.data.images")
@patch("src.materials.material_system.create_material")
@patch("src.materials.material_system.get_texture_asset_filepath")
@patch("src.materials.material_system.is_full_uv_rect", return_value=True)
def test_material_for_spots_zone_from_image_asset_loads_and_tags(
    _mock_full: MagicMock,
    mock_get_path: MagicMock,
    mock_create: MagicMock,
    mock_images: MagicMock,
    mock_wire: MagicMock,
) -> None:
    from src.materials.material_system import material_for_spots_zone_from_image_asset

    mock_get_path.return_value = Path("/tmp/plate.png")
    img = MagicMock()
    img.name = "spotimg"
    img.size = (32, 32)
    mock_images.load.return_value = img
    mat = MagicMock()
    mock_create.return_value = mat

    out = material_for_spots_zone_from_image_asset(
        base_palette_name="enemy_acid",
        finish="glossy",
        asset_id="demo_textures3",
        zone_hex_fallback="ffffff",
        instance_suffix="spot_plate",
        uv_rect=None,
    )
    assert out is mat
    mock_wire.assert_called_once()
    mat.__setitem__.assert_any_call("blobert_spot_image_name", "spotimg")


@patch("src.materials.material_system._wire_spot_plate_image_to_principled")
@patch("src.materials.material_system.bpy.data.images")
@patch("src.materials.material_system.create_material")
@patch("src.materials.material_system.get_texture_asset_filepath")
@patch("src.materials.material_system.resolved_asset_path_for_image_sampling")
@patch("src.materials.material_system.is_full_uv_rect", return_value=False)
def test_material_for_spots_zone_from_image_uses_resolved_crop_path(
    _mock_full: MagicMock,
    mock_resolved: MagicMock,
    mock_get_path: MagicMock,
    mock_create: MagicMock,
    mock_images: MagicMock,
    mock_wire: MagicMock,
) -> None:
    from src.materials.material_system import material_for_spots_zone_from_image_asset

    full_path = Path("/tmp/full_atlas.png")
    crop_path = Path("/tmp/crop.png")
    mock_get_path.return_value = full_path
    mock_resolved.return_value = crop_path
    img = MagicMock()
    img.name = "i2"
    img.size = (8, 8)
    mock_images.load.return_value = img
    mat = MagicMock()
    mock_create.return_value = mat

    material_for_spots_zone_from_image_asset(
        base_palette_name="enemy_acid",
        finish="default",
        asset_id="atlas1",
        zone_hex_fallback="ffffff",
        instance_suffix="sp",
        uv_rect=(0.0, 0.0, 0.5, 0.5),
    )
    mock_images.load.assert_called_once()
    assert mock_images.load.call_args[0][0] == str(crop_path)
    args, kwargs = mock_wire.call_args
    assert kwargs.get("use_atlas_mapping") is False


def test_spot_bg_rgba_endpoints_branches() -> None:
    from src.materials.material_system import _spot_bg_rgba_endpoints

    g = GradientFill(hex_a="ff0000", hex_b="00ff00", direction="horizontal")
    a, b = _spot_bg_rgba_endpoints(g, "ffffff")
    assert len(a) == 4 and len(b) == 4

    g_empty = GradientFill(hex_a="", hex_b="", direction="horizontal")
    a2, b2 = _spot_bg_rgba_endpoints(g_empty, "aabbcc")
    assert a2 == b2

    solid = SolidFill(hex_value="112233")
    s1, s2 = _spot_bg_rgba_endpoints(solid, "")
    assert s1 == s2

    img = ImageFill(asset_id="x", uv_rect=None)
    u, v = _spot_bg_rgba_endpoints(img, "ffffff")
    assert u == (1.0, 1.0, 1.0, 1.0) == v


def test_spot_bg_rgba_gradient_normalize_all_empty_uses_zone_hex() -> None:
    from src.materials.material_system import _spot_bg_rgba_endpoints

    with patch("src.materials.material_system.pattern_normalize_hex6", return_value=""):
        g = GradientFill(hex_a="xx", hex_b="yy", direction="horizontal")
        a, b = _spot_bg_rgba_endpoints(g, "ccddee")
    assert a == b


@patch("src.materials.material_system.write_rgba_buffer_to_gradients_png", side_effect=OSError("fail"))
@patch("src.materials.material_system.log_spots_composite")
def test_write_spot_background_underlay_png_failure_returns_none(
    _log: MagicMock,
    _write: MagicMock,
) -> None:
    from src.materials.material_system import _write_spot_background_underlay_png

    out = _write_spot_background_underlay_png(
        zone="body",
        spot_pattern_id="pat",
        width=2,
        height=2,
        spot_bg=SolidFill(hex_value="ffffff"),
        zone_hex="000000",
    )
    assert out is None


@patch("src.materials.material_system.log_spots_composite")
def test_write_spot_background_underlay_png_success_returns_path(
    _log: MagicMock,
    tmp_path: Path,
) -> None:
    from src.materials.material_system import _write_spot_background_underlay_png

    out_png = tmp_path / "underlay.png"
    out_png.write_bytes(b"\x89PNG\r\n\x1a\n")

    with patch(
        "src.materials.material_system.write_rgba_buffer_to_gradients_png",
        return_value=out_png,
    ):
        out = _write_spot_background_underlay_png(
            zone="body",
            spot_pattern_id="pat",
            width=2,
            height=2,
            spot_bg=SolidFill(hex_value="ffffff"),
            zone_hex="000000",
        )
    assert out is out_png
    assert _log.called


def test_resolve_spots_composite_underlay_primary_background_image() -> None:
    settings = _zone_options(background_fill=ImageFill(asset_id="under_tex", uv_rect=None))
    with patch("src.materials.material_system.log_spots_composite"):
        aid, path = resolve_spots_composite_underlay(
            zone="body",
            build_options={},
            zone_feature=None,
            settings=settings,
            spot_pattern_id="plate_tex",
        )
    assert aid == "under_tex"
    assert path is None


@patch("src.materials.material_system.resolve_zone_color_image_asset_id", return_value="zone_bg")
def test_resolve_spots_composite_underlay_zone_fallback(mock_zone: MagicMock) -> None:
    settings = _zone_options(background_fill=SolidFill(hex_value="ff0000"))
    with patch("src.materials.material_system.log_spots_composite"):
        aid, path = resolve_spots_composite_underlay(
            zone="body",
            build_options={},
            zone_feature=None,
            settings=settings,
            spot_pattern_id="plate_tex",
        )
    assert aid == "zone_bg"
    assert path is None
    mock_zone.assert_called_once()


def test_resolve_spots_composite_underlay_empty_spot_pattern() -> None:
    settings = _zone_options()
    aid, path = resolve_spots_composite_underlay(
        zone="body",
        build_options={},
        zone_feature=None,
        settings=settings,
        spot_pattern_id="",
    )
    assert aid == "" and path is None


@patch("src.materials.material_system.get_texture_asset_filepath", side_effect=ValueError("bad"))
def test_resolve_spots_composite_underlay_spot_path_resolve_error(_gp: MagicMock) -> None:
    settings = _zone_options()
    with patch("src.materials.material_system.log_spots_composite"):
        aid, path = resolve_spots_composite_underlay(
            zone="body",
            build_options={},
            zone_feature=None,
            settings=settings,
            spot_pattern_id="missing_asset",
        )
    assert aid == "" and path is None


def test_resolve_spots_composite_underlay_spot_file_missing(tmp_path: Path) -> None:
    settings = _zone_options()
    ghost = tmp_path / "nope.png"
    with patch("src.materials.material_system.get_texture_asset_filepath", return_value=ghost):
        with patch("src.materials.material_system.log_spots_composite"):
            aid, path = resolve_spots_composite_underlay(
                zone="body",
                build_options={},
                zone_feature=None,
                settings=settings,
                spot_pattern_id="x",
            )
    assert aid == "" and path is None


def test_resolve_spots_composite_underlay_invalid_png_header(tmp_path: Path) -> None:
    settings = _zone_options()
    bad_png = tmp_path / "bad.png"
    bad_png.write_bytes(b"not a png")
    with patch("src.materials.material_system.get_texture_asset_filepath", return_value=bad_png):
        with patch("src.materials.material_system.log_spots_composite"):
            aid, path = resolve_spots_composite_underlay(
                zone="body",
                build_options={},
                zone_feature=None,
                settings=settings,
                spot_pattern_id="x",
            )
    assert aid == "" and path is None


@patch("src.materials.material_system._write_spot_background_underlay_png", return_value=Path("/tmp/u.png"))
@patch("src.materials.material_system.read_png_ihdr_dimensions", return_value=(4, 4))
@patch("src.materials.material_system.get_texture_asset_filepath")
def test_resolve_spots_composite_underlay_synthesizes_from_plate(
    mock_get_path: MagicMock,
    _mock_dim: MagicMock,
    _mock_write: MagicMock,
    tmp_path: Path,
) -> None:
    from src.materials import gradient_generator as gg

    png = tmp_path / "plate.png"
    pix = gg.gradient_image_pixel_buffer(2, 2, (0.2, 0.2, 0.2, 1.0), (0.3, 0.3, 0.3, 1.0), "horizontal")
    png.write_bytes(gg._create_png(2, 2, pix))
    mock_get_path.return_value = png
    settings = _zone_options(background_fill=GradientFill(hex_a="ff0000", hex_b="0000ff", direction="horizontal"))
    with patch("src.materials.material_system.log_spots_composite"):
        aid, out_path = resolve_spots_composite_underlay(
            zone="body",
            build_options={},
            zone_feature=None,
            settings=settings,
            spot_pattern_id="plate1",
        )
    assert aid == ""
    assert out_path == Path("/tmp/u.png")
