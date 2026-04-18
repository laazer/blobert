"""Behavioral tests for zone gradient → packed image → TexImage (glTF-exportable path).

Previous tests mocked ``_add_uv_gradient_to_principled``, so regressions in ``bpy.data.images``
or ``_gradient_image_pixel_buffer`` were invisible. These tests lock the real wiring.

What this file does *not* catch: ``bpy.ops.export_scene.gltf`` output (run Blender once and
parse the GLB JSON + embedded PNG if a regression is viewer-only).
"""

from __future__ import annotations

from unittest import skip
from unittest.mock import MagicMock, patch

from src.materials import material_system as ms


def test_gradient_buffer_horizontal_length_and_endpoints() -> None:
    """256×4 horizontal strip: left ≈ color_a, right ≈ color_b (bottom row, left/right)."""
    a = (1.0, 0.0, 0.0, 1.0)
    b = (0.0, 0.0, 1.0, 1.0)
    buf = ms._gradient_image_pixel_buffer(256, 4, a, b, "horizontal")
    assert len(buf) == 256 * 4 * 4
    # Bottom row y=0: x=0 (left), x=255 (right)
    i0 = (0 * 256 + 0) * 4
    i1 = (0 * 256 + 255) * 4
    assert buf[i0] > 0.95 and buf[i0 + 2] < 0.1
    assert buf[i1 + 2] > 0.95 and buf[i1] < 0.1


def test_gradient_buffer_vertical_dimensions() -> None:
    buf = ms._gradient_image_pixel_buffer(4, 256, (1.0, 0.0, 0.0, 1.0), (0.0, 1.0, 0.0, 1.0), "vertical")
    assert len(buf) == 4 * 256 * 4


def test_gradient_buffer_radial_center_vs_corner() -> None:
    a = (1.0, 0.0, 0.0, 1.0)
    b = (0.0, 0.0, 1.0, 1.0)
    buf = ms._gradient_image_pixel_buffer(128, 128, a, b, "radial")
    assert len(buf) == 128 * 128 * 4
    # Center (t≈0) → color_a; corner (t larger) → closer to b
    mid = 64
    ci = (mid * 128 + mid) * 4
    corner_i = (0 * 128 + 0) * 4
    assert buf[ci] > buf[corner_i]


def test_sanitize_image_label() -> None:
    assert ms._sanitize_image_label("body_tex_grad!") == "body_tex_grad_"
    assert ms._sanitize_image_label("") == "gradient"


def _make_node_socket(socket_type: str = "base_color"):
    socket = MagicMock()
    socket.links = [MagicMock()]
    return socket


def _make_principled_bsdf():
    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bsdf.inputs = {"Base Color": _make_node_socket()}
    return bsdf


def _make_principled_by_idname():
    bsdf = MagicMock()
    bsdf.type = "SHADER"
    bsdf.bl_idname = "ShaderNodeBsdfPrincipled"
    bsdf.inputs = {"Base Color": _make_node_socket()}
    return bsdf


def _make_mock_node_collection(bsdf_maker):
    class _Nodes:
        def __iter__(self):
            return iter([bsdf_maker()])

        def new(self, *, type: str):
            n = MagicMock()
            n.type = type
            if type == "ShaderNodeTexImage":
                n.inputs = {"Vector": MagicMock()}
                n.outputs = {"Color": MagicMock()}
            elif type == "ShaderNodeUVMap":
                n.outputs = {"UV": MagicMock()}
            return n

    return _Nodes()


class _MockLinks:
    def __init__(self) -> None:
        self.new_calls: list = []

    def remove(self, _lk):
        pass

    def new(self, *a):
        self.new_calls.append(a)


def _fake_mat_with_bsdf():
    nt = MagicMock()
    nt.nodes = _make_mock_node_collection(_make_principled_bsdf)
    nt.links = _MockLinks()
    mat = MagicMock()
    mat.node_tree = nt
    return mat


def _fake_mat_with_idname_bsdf():
    nt = MagicMock()
    nt.nodes = _make_mock_node_collection(_make_principled_by_idname)
    nt.links = _MockLinks()
    mat = MagicMock()
    mat.node_tree = nt
    return mat


class _RecordingImage:
    def __init__(self) -> None:
        self.pixels: list[float] | None = None
        self.colorspace_settings = MagicMock()
        self.packed = False

    def pack(self) -> None:
        self.packed = True

    def update(self) -> None:
        pass


@skip("TODO: test needs updating for new file-based PNG creation in gradient_generator")
def test_material_for_gradient_zone_calls_images_new_without_mocking_uv_hook() -> None:
    """Full ``_material_for_gradient_zone`` must create a packed image + tex (not only mock)."""
    mat = _fake_mat_with_bsdf()
    captured: dict[str, object] = {}
    recording = _RecordingImage()

    def _images_new(**kwargs):
        captured.update(kwargs)
        return recording

    with (
        patch.object(ms, "create_material", return_value=mat),
        patch("src.materials.gradient_generator.bpy.data.images.load", return_value=recording),
        patch("src.materials.gradient_generator.Path.mkdir"),
        patch("src.materials.gradient_generator.Path.write_bytes"),
    ):
        ms._material_for_gradient_zone(
            base_palette_name="Organic_Brown",
            finish="default",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="",
            instance_suffix="unit_grad",
        )
    assert recording.packed
    assert recording.pixels is not None
    assert len(recording.pixels) == 256 * 4 * 4
    assert len(mat.node_tree.links.new_calls) >= 2


def test_add_uv_gradient_finds_bsdf_by_bl_idname_when_type_not_bsdf_principled() -> None:
    """Regression: some Blender builds set ``bl_idname`` but not ``type == BSDF_PRINCIPLED``."""
    mat = _fake_mat_with_idname_bsdf()
    recording = _RecordingImage()

    with patch("src.materials.gradient_generator.bpy.data.images.load", return_value=recording):
        ms._add_uv_gradient_to_principled(mat, (1, 0, 0, 1), (0, 0, 1, 1), "horizontal")
    assert len(mat.node_tree.links.new_calls) >= 2
    assert recording.pixels is not None
    assert max(recording.pixels) > 0.01, "gradient image must not be all zeros (black export)"


def test_material_for_gradient_zone_red_blue_hex_pixels_not_black() -> None:
    """Packed image must contain visible red/blue channels (catches float_buffer / export black)."""
    mat = _fake_mat_with_bsdf()
    recording = _RecordingImage()

    with (
        patch.object(ms, "create_material", return_value=mat),
        patch("src.materials.gradient_generator.bpy.data.images.load", return_value=recording),
    ):
        ms._material_for_gradient_zone(
            base_palette_name="Organic_Brown",
            finish="default",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="",
            instance_suffix="unit_grad",
        )
    assert recording.pixels is not None
    assert max(recording.pixels) > 0.5
    assert any(recording.pixels[i] > 0.9 for i in range(0, min(len(recording.pixels), 400), 4))


def test_apply_zone_texture_pattern_invokes_images_new_when_not_mocking_gradient_hook() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    mat = _fake_mat_with_bsdf()
    recording = _RecordingImage()

    def _images_new(**kwargs):
        return recording

    with (
        patch.object(ms, "create_material", return_value=mat),
        patch("src.materials.material_system.bpy.data.images.new", side_effect=_images_new),
    ):
        ms.apply_zone_texture_pattern_overrides(
            {"body": base},
            {
                "feat_body_texture_mode": "gradient",
                "feat_body_texture_grad_color_a": "ff0000",
                "feat_body_texture_grad_color_b": "00ff00",
            },
        )
    assert recording.packed
    assert recording.pixels is not None
    assert len(recording.pixels) == 256 * 4 * 4
