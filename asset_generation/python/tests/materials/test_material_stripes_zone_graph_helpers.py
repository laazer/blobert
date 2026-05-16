"""Direct coverage for material_stripes_zone internal graph helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.materials.material_stripes_zone import (
    _build_directional_dot_product,
    _build_stripe_band_selector,
    _fill_hex,
)
from src.materials.material_types import GradientFill, ImageFill, SolidFill


def test_fill_hex_dispatch() -> None:
    assert _fill_hex(SolidFill(hex_value="aa")) == "aa"
    assert _fill_hex(GradientFill(hex_a="bb", hex_b="cc", direction="h")) == "bb"
    assert _fill_hex(ImageFill(asset_id="x", uv_rect=None)) == ""


def test_build_directional_dot_product_links_math_chain() -> None:
    sep = MagicMock()
    sep.outputs = {"X": MagicMock(), "Y": MagicMock(), "Z": MagicMock()}
    created: list[str] = []

    class _Nodes:
        def new(self, type: str) -> MagicMock:  # noqa: A002
            created.append(type)
            m = MagicMock()
            m.type = type
            m.operation = ""
            m.inputs = {}
            for i in range(3):
                slot = MagicMock()
                slot.default_value = 0.0
                m.inputs[i] = slot
            m.outputs = {"Value": MagicMock()}
            return m

    links_calls: list[tuple[object, object]] = []

    class _Links:
        def new(self, a, b) -> None:
            links_calls.append((a, b))

    out = _build_directional_dot_product(_Nodes(), _Links(), sep, 1.0, 0.0, 0.0)
    assert out is not None
    assert "ShaderNodeMath" in created
    assert links_calls


def test_build_stripe_band_selector_returns_none_when_mix_inputs_missing() -> None:
    dot = MagicMock()
    dot.outputs = {"Value": MagicMock()}
    nodes = MagicMock()

    def new_node(type: str) -> MagicMock:  # noqa: A002
        m = MagicMock()
        m.type = type
        m.inputs = {0: MagicMock(), 1: MagicMock()}
        m.inputs[0].default_value = 0.0
        m.inputs[1].default_value = 0.0
        m.outputs = {"Value": MagicMock(), "Color": MagicMock()}
        if "MixRGB" in type:
            m.inputs = {"Fac": None, "Color1": MagicMock(), "Color2": MagicMock()}
        return m

    nodes.new.side_effect = new_node
    links = MagicMock()
    assert (
        _build_stripe_band_selector(
            nodes,
            links,
            dot,
            2.0,
            0.1,
            (1.0, 0.0, 0.0, 1.0),
            (0.0, 1.0, 0.0, 1.0),
        )
        is None
    )


def test_build_stripe_band_selector_returns_color_output() -> None:
    dot = MagicMock()
    dot.outputs = {"Value": MagicMock()}
    color_sock = MagicMock()
    mix = MagicMock()
    mix.blend_type = "MIX"
    fac = MagicMock()
    c1 = MagicMock()
    c2 = MagicMock()
    mix.inputs = {"Fac": fac, "Color1": c1, "Color2": c2}
    mix.outputs = {"Color": color_sock}

    seq = []

    def new_node(type: str) -> MagicMock:  # noqa: A002
        m = MagicMock()
        m.type = type
        m.operation = ""
        m.inputs = {0: MagicMock(), 1: MagicMock()}
        for i in range(2):
            m.inputs[i].default_value = 0.0
        m.outputs = {"Value": MagicMock()}
        seq.append(type)
        if type == "ShaderNodeMixRGB":
            return mix
        return m

    nodes = MagicMock()
    nodes.new.side_effect = new_node
    links = MagicMock()
    out = _build_stripe_band_selector(
        nodes,
        links,
        dot,
        2.0,
        0.0,
        (1.0, 0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0, 1.0),
    )
    assert out is color_sock


def test_add_object_space_stripes_links_when_band_selector_returns_color() -> None:
    from unittest.mock import patch

    from src.materials.material_stripes_zone import (
        _add_object_space_stripes_to_principled,
    )

    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bc = MagicMock()
    bc.links = [MagicMock()]
    bsdf.inputs = {"Base Color": bc}

    tex_coord = MagicMock()
    obj_out = MagicMock(name="obj_out")
    tex_coord.outputs = {"Object": obj_out}

    separate = MagicMock()
    separate.inputs = {"Vector": MagicMock()}
    separate.outputs = {"X": MagicMock(), "Y": MagicMock(), "Z": MagicMock()}

    def new_node(t: str) -> MagicMock:
        if t == "ShaderNodeTexCoord":
            return tex_coord
        if t == "ShaderNodeSeparateXYZ":
            return separate
        m = MagicMock()
        m.type = t
        m.operation = ""
        m.inputs = {}
        for i in range(3):
            slot = MagicMock()
            slot.default_value = 0.0
            m.inputs[i] = slot
        m.outputs = {"Value": MagicMock()}
        return m

    class _Nodes:
        def __iter__(self):
            return iter([bsdf])

        def new(self, type: str) -> MagicMock:  # noqa: A002
            return new_node(type)

    links = MagicMock()
    nt = MagicMock()
    nt.nodes = _Nodes()
    nt.links = links
    mat = MagicMock()
    mat.node_tree = nt

    color_out = MagicMock()
    with (
        patch(
            "src.materials.material_stripes_zone._stripe_direction_vector",
            return_value=(1.0, 0.0, 0.0),
        ),
        patch(
            "src.materials.material_stripes_zone._build_stripe_band_selector",
            return_value=color_out,
        ),
    ):
        _add_object_space_stripes_to_principled(
            mat=mat,
            stripe_rgba=(1.0, 0.0, 0.0, 1.0),
            bg_rgba=(0.0, 1.0, 0.0, 1.0),
            stripe_width=0.5,
            stripe_preset="doplar",
            rot_yaw_deg=0.0,
            rot_pitch_deg=0.0,
            rot_roll_deg=0.0,
        )
    assert links.new.called


def test_add_object_space_stripes_returns_without_node_tree() -> None:
    from src.materials.material_stripes_zone import (
        _add_object_space_stripes_to_principled,
    )

    mat = MagicMock()
    mat.node_tree = None
    _add_object_space_stripes_to_principled(
        mat=mat,
        stripe_rgba=(1.0, 0.0, 0.0, 1.0),
        bg_rgba=(0.0, 1.0, 0.0, 1.0),
        stripe_width=0.5,
        stripe_preset="doplar",
        rot_yaw_deg=0.0,
        rot_pitch_deg=0.0,
        rot_roll_deg=0.0,
    )


def test_add_object_space_stripes_returns_without_bsdf() -> None:
    from src.materials.material_stripes_zone import (
        _add_object_space_stripes_to_principled,
    )

    class _Empty:
        def __iter__(self):
            return iter([])

    nt = MagicMock()
    nt.nodes = _Empty()
    nt.links = MagicMock()
    mat = MagicMock()
    mat.node_tree = nt
    _add_object_space_stripes_to_principled(
        mat=mat,
        stripe_rgba=(1.0, 0.0, 0.0, 1.0),
        bg_rgba=(0.0, 1.0, 0.0, 1.0),
        stripe_width=0.5,
        stripe_preset="doplar",
        rot_yaw_deg=0.0,
        rot_pitch_deg=0.0,
        rot_roll_deg=0.0,
    )


def test_add_object_space_stripes_returns_without_base_color_socket() -> None:
    from src.materials.material_stripes_zone import (
        _add_object_space_stripes_to_principled,
    )

    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    ins = MagicMock()

    def _no_base_color(_k: str) -> None:
        return None

    ins.get = _no_base_color
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
    _add_object_space_stripes_to_principled(
        mat=mat,
        stripe_rgba=(1.0, 0.0, 0.0, 1.0),
        bg_rgba=(0.0, 1.0, 0.0, 1.0),
        stripe_width=0.5,
        stripe_preset="doplar",
        rot_yaw_deg=0.0,
        rot_pitch_deg=0.0,
        rot_roll_deg=0.0,
    )


def test_add_object_space_stripes_returns_without_object_output() -> None:
    from src.materials.material_stripes_zone import (
        _add_object_space_stripes_to_principled,
    )

    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bc = MagicMock()
    bc.links = []
    bsdf.inputs = {"Base Color": bc}

    tex_coord = MagicMock()
    tex_coord.outputs = MagicMock()
    tex_coord.outputs.get = MagicMock(return_value=None)

    def new_node(t: str) -> MagicMock:
        if t == "ShaderNodeTexCoord":
            return tex_coord
        m = MagicMock()
        m.type = t
        return m

    class _Nodes:
        def __iter__(self):
            return iter([bsdf])

        def new(self, type: str) -> MagicMock:  # noqa: A002
            return new_node(type)

    nt = MagicMock()
    nt.nodes = _Nodes()
    nt.links = MagicMock()
    mat = MagicMock()
    mat.node_tree = nt

    _add_object_space_stripes_to_principled(
        mat=mat,
        stripe_rgba=(1.0, 0.0, 0.0, 1.0),
        bg_rgba=(0.0, 1.0, 0.0, 1.0),
        stripe_width=0.5,
        stripe_preset="doplar",
        rot_yaw_deg=0.0,
        rot_pitch_deg=0.0,
        rot_roll_deg=0.0,
    )
