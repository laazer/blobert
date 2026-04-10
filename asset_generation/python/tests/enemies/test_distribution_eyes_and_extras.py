"""Random vs uniform distribution for eyes and zone extras (ticket 16)."""

from __future__ import annotations

import math
import random
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.enemies.animated_spider import AnimatedSpider
from src.enemies.zone_geometry_extras_attach import (
    _append_body_ellipsoid_extras,
    _append_head_ellipsoid_extras,
)
from src.utils import animated_build_options as abo
from src.utils.animated_build_options import options_for_enemy
from src.utils.placement_clustering import uniform_arc_angles


def test_options_merge_distribution_and_placement_seed() -> None:
    o = options_for_enemy(
        "slug",
        {
            "extra_zone_body_distribution": "random",
            "extra_zone_head_uniform_shape": "ring",
            "placement_seed": 42,
        },
    )
    assert o["placement_seed"] == 42
    assert o["zone_geometry_extras"]["body"]["distribution"] == "random"
    assert o["zone_geometry_extras"]["head"]["uniform_shape"] == "ring"


def test_sanitize_invalid_distribution_and_shape() -> None:
    got = abo._sanitize_zone_geometry_extras(
        "slug",
        {"body": {"distribution": "chaos", "uniform_shape": "torus"}},
    )
    assert got["body"]["distribution"] == "uniform"
    assert got["body"]["uniform_shape"] == "arc"


def test_eye_dirs_random_single_eye() -> None:
    mats: dict[str, object] = {}
    hc = SimpleNamespace(x=1.0, y=0.0, z=0.3)
    hs = 1.0
    s = AnimatedSpider(
        "spider",
        mats,
        random.Random(0),
        build_options={"eye_distribution": "random", "placement_seed": 3},
    )
    eyes = s._eye_dirs_random(1, hc, hs)
    assert len(eyes) == 1
    assert abs(float(eyes[0].x) - 1.0) < 1e-5


def test_spider_uniform_vs_random_eye_dirs_differ() -> None:
    mats: dict[str, object] = {}
    hc = SimpleNamespace(x=1.0, y=0.0, z=0.3)
    hs = 1.0
    su = AnimatedSpider(
        "spider",
        mats,
        random.Random(0),
        build_options={"eye_count": 5, "eye_distribution": "uniform", "placement_seed": 1},
    )
    sr = AnimatedSpider(
        "spider",
        mats,
        random.Random(0),
        build_options={"eye_count": 5, "eye_distribution": "random", "placement_seed": 1},
    )
    u = su._eye_dirs_uniform(5, hc, hs)
    r = sr._eye_dirs_random(5, hc, hs)
    ut = tuple((round(v.x, 5), round(v.y, 5), round(v.z, 5)) for v in u)
    rt = tuple((round(v.x, 5), round(v.y, 5), round(v.z, 5)) for v in r)
    assert ut != rt


def test_uniform_arc_is_deterministic() -> None:
    th = 2.0 * math.pi
    a0 = uniform_arc_angles(0, 4, theta_lo=0.0, theta_hi=th, phi_lo=0.1, phi_hi=3.0, clustering=0.3)
    a1 = uniform_arc_angles(0, 4, theta_lo=0.0, theta_hi=th, phi_lo=0.1, phi_hi=3.0, clustering=0.3)
    assert a0 == a1


def test_body_uniform_vs_random_different_cone_locations() -> None:
    class _M:
        build_options: dict
        parts: list
        rng: random.Random

    m = _M()
    m.build_options = {"placement_seed": 7}
    m.parts = []
    m.rng = random.Random(0)
    slot: dict[str, MagicMock | None] = {"body": MagicMock()}
    feats = None
    spec_base = {
        "kind": "spikes",
        "spike_count": 2,
        "uniform_shape": "arc",
        "clustering": 0.2,
        "spike_shape": "cone",
        "finish": "default",
        "hex": "",
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
    }

    def run(dist: str) -> list[tuple[float, float, float]]:
        captured: list[tuple[float, float, float]] = []

        def cone_cb(*_a, location, **_kw):
            captured.append((float(location[0]), float(location[1]), float(location[2])))
            return MagicMock()

        spec = {**spec_base, "distribution": dist}
        with patch("src.enemies.zone_geometry_extras_attach.create_cone", side_effect=cone_cb):
            with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
                with patch(
                    "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                    return_value=MagicMock(),
                ):
                    _append_body_ellipsoid_extras(
                        m, spec, slot, feats, 0.0, 0.0, 0.5, 1.0, 0.5, 0.6
                    )
        return captured

    u = run("uniform")
    r = run("random")
    assert u != r


def test_body_uniform_ring_spikes_place_cones() -> None:
    class _M:
        build_options: dict
        parts: list
        rng: random.Random

    m = _M()
    m.build_options = {"placement_seed": 1}
    m.parts = []
    m.rng = random.Random(0)
    slot: dict[str, MagicMock | None] = {"body": MagicMock()}
    spec = {
        "kind": "spikes",
        "spike_count": 2,
        "uniform_shape": "ring",
        "distribution": "uniform",
        "clustering": 0.2,
        "spike_shape": "cone",
        "finish": "default",
        "hex": "",
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
    }
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", return_value=MagicMock()):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_body_ellipsoid_extras(m, spec, slot, None, 0.0, 0.0, 0.5, 1.0, 0.5, 0.6)
    assert len(m.parts) == 2


def test_head_random_spikes_and_bulbs_append_parts() -> None:
    class _M:
        build_options: dict
        parts: list
        rng: random.Random

    m = _M()
    m.build_options = {"placement_seed": 11}
    m.parts = []
    m.rng = random.Random(0)
    slot: dict[str, MagicMock | None] = {"head": MagicMock()}
    base_place = {
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
    }
    spike_spec = {
        "kind": "spikes",
        "spike_count": 2,
        "distribution": "random",
        "uniform_shape": "arc",
        "clustering": 0.3,
        "spike_shape": "cone",
        "finish": "default",
        "hex": "",
        **base_place,
    }
    bulb_spec = {
        "kind": "bulbs",
        "bulb_count": 2,
        "distribution": "random",
        "uniform_shape": "arc",
        "clustering": 0.3,
        "finish": "default",
        "hex": "",
        **base_place,
    }
    with patch("src.enemies.zone_geometry_extras_attach.create_cone", return_value=MagicMock()):
        with patch("src.enemies.zone_geometry_extras_attach.create_sphere", return_value=MagicMock()):
            with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
                with patch(
                    "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                    return_value=MagicMock(),
                ):
                    _append_head_ellipsoid_extras(m, spike_spec, slot, None, 0.0, 0.0, 0.4, 0.5, 0.5, 0.45)
                    assert len(m.parts) == 2
                    m.parts.clear()
                    _append_head_ellipsoid_extras(m, bulb_spec, slot, None, 0.0, 0.0, 0.4, 0.5, 0.5, 0.45)
                    assert len(m.parts) == 2


def test_head_uniform_ring_bulbs() -> None:
    class _M:
        build_options: dict
        parts: list
        rng: random.Random

    m = _M()
    m.build_options = {"placement_seed": 2}
    m.parts = []
    m.rng = random.Random(0)
    slot: dict[str, MagicMock | None] = {"head": MagicMock()}
    spec = {
        "kind": "bulbs",
        "bulb_count": 2,
        "distribution": "uniform",
        "uniform_shape": "ring",
        "clustering": 0.25,
        "finish": "default",
        "hex": "",
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
    }
    with patch("src.enemies.zone_geometry_extras_attach.create_sphere", return_value=MagicMock()):
        with patch("src.enemies.zone_geometry_extras_attach.apply_material_to_object"):
            with patch(
                "src.enemies.zone_geometry_extras_attach.material_for_zone_geometry_extra",
                return_value=MagicMock(),
            ):
                _append_head_ellipsoid_extras(m, spec, slot, None, 0.0, 0.0, 0.4, 0.5, 0.5, 0.45)
    assert len(m.parts) == 2
