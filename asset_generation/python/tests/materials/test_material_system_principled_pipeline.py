"""PMCP-1 / PMCP-2: principled defaults and organic detail (no real Blender)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.materials import material_system as ms
from src.materials.material_system import (
    _ORGANIC_BASE_COLOR_DETAIL_FAC,
    add_metallic_texture,
    add_organic_texture,
    create_material,
)


class _RecordingLinks:
    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    def new(self, out_sock, in_sock) -> None:
        self.calls.append((out_sock, in_sock))


class _FakeNodes:
    def __init__(self) -> None:
        self._by_type: dict[str, MagicMock] = {}

    def clear(self) -> None:
        self._by_type.clear()

    def new(self, type: str) -> MagicMock:  # noqa: A002 — Blender API name
        m = MagicMock()
        m.type = type
        m.inputs = MagicMock()
        m.outputs = MagicMock()
        if type == "ShaderNodeTexNoise":
            m.outputs = {"Fac": "noise_out"}
        elif type == "ShaderNodeValToRGB":
            m.outputs = {"Color": "ramp_out"}
            m.inputs = {"Fac": "ramp_in"}
        elif type == "ShaderNodeMixRGB":

            class _MixIn:
                def __init__(self) -> None:
                    self.fac = MagicMock()
                    self.fac.default_value = 0.0

                def __getitem__(self, name: str):
                    if name == "Fac":
                        return self.fac
                    if name == "Color1":
                        return MagicMock()
                    if name == "Color2":
                        return MagicMock()
                    return MagicMock()

            mix_in = _MixIn()
            m.inputs = mix_in
            m.outputs = {"Color": "mix_color_out"}
            m._mix_fac_holder = mix_in.fac
        self._by_type[type] = m
        return m


def _bsdf_with_roughness() -> tuple[MagicMock, MagicMock]:
    rough = MagicMock()
    rough.name = "Roughness"
    base = MagicMock()
    base.name = "Base Color"
    bsdf = MagicMock()
    bsdf.inputs = {"Base Color": base, "Roughness": rough, "Metallic": MagicMock()}
    return bsdf, rough


def test_add_organic_texture_does_not_link_to_roughness() -> None:
    """PMCP-1: organic handler must not replace principled roughness with noise."""
    links = _RecordingLinks()
    nodes = _FakeNodes()
    bsdf, rough_in = _bsdf_with_roughness()
    base_color = (0.4, 0.5, 0.6, 1.0)
    add_organic_texture(MagicMock(), nodes, links, bsdf, base_color)
    rough_targets = [inp for _o, inp in links.calls if inp is rough_in]
    assert not rough_targets, "organic texture must not drive Roughness socket"


def test_add_organic_texture_mix_fac_matches_named_constant() -> None:
    links = _RecordingLinks()
    nodes = _FakeNodes()
    bsdf, _ = _bsdf_with_roughness()
    add_organic_texture(MagicMock(), nodes, links, bsdf, (1.0, 1.0, 1.0, 1.0))
    mix = nodes._by_type["ShaderNodeMixRGB"]
    assert mix._mix_fac_holder.default_value == _ORGANIC_BASE_COLOR_DETAIL_FAC


def test_add_metallic_texture_does_not_create_roughness_links() -> None:
    """PMCP-1: metallic handler must not attach noise to roughness."""
    links = _RecordingLinks()
    nodes = _FakeNodes()
    bsdf, rough_in = _bsdf_with_roughness()
    add_metallic_texture(MagicMock(), nodes, links, bsdf, (0.5, 0.5, 0.5, 1.0))
    assert links.calls == []


def test_create_material_toxic_green_organic_no_roughness_link() -> None:
    """Integration-style check through create_material with a fake node graph."""
    links_proxy = _RecordingLinks()

    def _patched_new(name: str):
        mat = MagicMock()
        mat.name = name
        nt = MagicMock()
        nodes = _FakeNodes()
        nt.nodes = nodes

        def _links_new(out_sock, in_sock):
            links_proxy.calls.append((out_sock, in_sock))

        nt.links.new = _links_new
        mat.node_tree = nt
        mat.blend_method = "OPAQUE"
        mat.use_nodes = True
        return mat

    with patch.object(ms.bpy.data.materials, "new", side_effect=_patched_new):
        create_material(
            "toxic_green",
            (0.2, 0.8, 0.3, 1.0),
            metallic=0.0,
            roughness=0.7,
            add_texture=True,
            force_surface=False,
            force_base_color=False,
        )
    roughness_links = [
        pair for pair in links_proxy.calls if getattr(pair[1], "name", None) == "Roughness"
    ]
    assert not roughness_links


def test_organic_detail_fac_stays_below_legacy_wash_ceiling() -> None:
    # CHECKPOINT: legacy organic multiply used Fac=0.3 — keep pipeline visibly more saturated.
    assert _ORGANIC_BASE_COLOR_DETAIL_FAC < 0.3
